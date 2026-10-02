from __future__ import annotations
import argparse, ast, csv, io, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data/work_graph.csv"
EVIDENCE = ROOT / "data/work_evidence.csv"
GATE = ROOT / "scripts/trust_gate.py"
OUT_MD = ROOT / "docs/WORK_MAP.md"
OUT_CSV = ROOT / "docs/WORK_STATUS.csv"

def rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def parts(value):
    return [x.strip() for x in (value or "").split(";") if x.strip()]

def gate_tests():
    tree = ast.parse(GATE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TESTS" for t in node.targets):
            return set(ast.literal_eval(node.value))
    raise ValueError("Trust Gate TESTS list not found")

def module(path):
    value = path.replace("\\", "/")
    return (value[:-3] if value.endswith(".py") else value).replace("/", ".")

def build():
    work = rows(GRAPH)
    evidence = rows(EVIDENCE)
    ids = {r["id"] for r in work}
    if len(ids) != len(work):
        raise ValueError("duplicate work item id")
    gate = gate_tests()
    ev = {x: [] for x in ids}
    for e in evidence:
        if e["work_item"] not in ids:
            raise ValueError("evidence references unknown work item: " + e["work_item"])
        ev[e["work_item"]].append(e)
    model = []
    for r in work:
        bd, pd = parts(r["build_dependencies"]), parts(r["proof_dependencies"])
        for dep in bd + pd:
            if dep not in ids:
                raise ValueError(f"{r['id']} references unknown dependency {dep}")
        impl, tests, system = parts(r["implementation_paths"]), parts(r["task_tests"]), parts(r["system_tests"])
        item = dict(r)
        item.update({
            "build": bd, "proof": pd, "owners": parts(r["owner_paths"]),
            "impl": impl, "tests": tests, "system": system, "evidence": ev[r["id"]],
            "integrated": any(e["evidence_type"] == "merged_pr" and e["result"] == "pass" for e in ev[r["id"]]),
            "impl_present": bool(impl) and all((ROOT / p).is_file() for p in impl),
            "tests_defined": bool(tests) and all((ROOT / p).is_file() for p in tests),
            "tests_gated": bool(tests) and all((ROOT / p).is_file() and module(p) in gate for p in tests),
            "system_defined": bool(system) and all((ROOT / p).is_file() for p in system),
            "system_gated": bool(system) and all((ROOT / p).is_file() and module(p) in gate for p in system),
        })
        model.append(item)
    by = {x["id"]: x for x in model}
    for x in model:
        x["deps_ready"] = all(by[d]["integrated"] for d in x["build"])
        if not x["deps_ready"]: state = "BLOCKED"
        elif not x["impl_present"]: state = "READY"
        elif not x["tests_defined"]: state = "IMPLEMENTED_NO_TEST"
        elif not x["tests_gated"]: state = "TEST_DEFINED_NOT_GATED"
        elif not x["integrated"]: state = "COMPONENT_GATE_WIRED"
        elif not x["system_gated"]: state = "INTEGRATED_COMPONENT_WIRED"
        else: state = "SYSTEM_PROOF_WIRED"
        x["state"] = state
    return model, evidence

def action(x, by):
    s = x["state"]
    if s == "BLOCKED":
        return "wait for " + ",".join(d for d in x["build"] if not by[d]["integrated"])
    return {
        "READY":"implement",
        "IMPLEMENTED_NO_TEST":"add task test",
        "TEST_DEFINED_NOT_GATED":"wire task test into Trust Gate",
        "COMPONENT_GATE_WIRED":"integrate",
        "INTEGRATED_COMPONENT_WIRED":"add/wire system proof",
        "SYSTEM_PROOF_WIRED":"observe system proof execution",
    }[s]

def status(model):
    by = {x["id"]: x for x in model}
    out = []
    for x in model:
        out.append({
            "id":x["id"], "goal":x["system_goal"], "title":x["title"], "priority":x["priority"],
            "state":x["state"], "deps_ready":"yes" if x["deps_ready"] else "no",
            "implementation":"yes" if x["impl_present"] else "no",
            "task_test":"yes" if x["tests_defined"] else "no",
            "task_gate":"yes" if x["tests_gated"] else "no",
            "integrated":"yes" if x["integrated"] else "no",
            "system_proof":"yes" if x["system_gated"] else "no",
            "next":action(x, by),
        })
    return out

def csv_text(model):
    data = status(model)
    s = io.StringIO(newline="")
    w = csv.DictWriter(s, fieldnames=list(data[0]), lineterminator="\n")
    w.writeheader(); w.writerows(data)
    return s.getvalue()

def render(model, evidence):
    by = {x["id"]: x for x in model}
    ready = [x["id"] for x in model if x["state"] == "READY"]
    debt = [x["id"] for x in model if x["integrated"] and x["tests_defined"] and not x["tests_gated"]]
    blocked = [x["id"] for x in model if x["state"] == "BLOCKED"]
    conflicts = []
    active = [x for x in model if x["state"] in {"READY","IMPLEMENTED_NO_TEST","TEST_DEFINED_NOT_GATED"}]
    for i,a in enumerate(active):
        for b in active[i+1:]:
            for p in sorted(set(a["owners"]) & set(b["owners"])):
                conflicts.append((a["id"], b["id"], p))
    lines = [
        "# Development Control Map","",
        "<!-- Generated from data/work_graph.csv + data/work_evidence.csv by scripts/work_map.py. -->","",
        "O CSV declara trabalho e evidência; estado operacional é derivado. Merge, teste existente e prova de sistema são dimensões separadas.","",
        "[Repository Map](REPOSITORY_MAP.md) · [Product Intent](PRODUCT_INTENT.md) · [Decisions](DECISIONS.md)","",
        "## Agora","",
        "- Ready: " + (", ".join(f"`{x}`" for x in ready) or "nenhum"),
        "- Dívida de verificação: " + (", ".join(f"`{x}`" for x in debt) or "nenhuma"),
        "- Bloqueados: " + (", ".join(f"`{x}`" for x in blocked) or "nenhum"),
        "- Conflitos de ownership acionáveis: " + str(len(conflicts)),"",
        "## Grafo","",
        "```mermaid","flowchart LR",
    ]
    nid = lambda s: "W_" + "".join(c if c.isalnum() else "_" for c in s)
    for x in model:
        lines.append(f'  {nid(x["id"])}["{x["id"]}<br/>{x["title"]}<br/>{x["state"]}"]')
    for x in model:
        for d in x["build"]: lines.append(f"  {nid(d)} -->|build| {nid(x['id'])}")
        for d in x["proof"]:
            if d not in x["build"]: lines.append(f"  {nid(d)} -.->|proof| {nid(x['id'])}")
    lines += ["```","","## Work board","",
        "| ID | Implementação | Teste | Gate | Merge | Prova sistema | Estado | Next |",
        "|---|---:|---:|---:|---:|---:|---|---|"]
    m = lambda v: "✓" if v else "—"
    for x in model:
        lines.append(f"| `{x['id']}` | {m(x['impl_present'])} | {m(x['tests_defined'])} | {m(x['tests_gated'])} | {m(x['integrated'])} | {m(x['system_gated'])} | `{x['state']}` | {action(x,by)} |")
    lines += ["","## Dívida de verificação",""]
    lines += [f"- `{x}`: teste existe e trabalho está integrado, mas o teste ainda não está no Trust Gate." for x in debt] or ["Nenhuma."]
    lines += ["","## Paralelismo",""]
    lines += [f"- `{a}` ↔ `{b}` colidem em `{p}`." for a,b,p in conflicts] or ["Nenhuma colisão de ownership entre trabalhos acionáveis."]
    lines += ["","## Evidência append-only","",
        "| Item | Tipo | Referência | Resultado | Escopo | Data | Nota |",
        "|---|---|---|---|---|---|---|"]
    for e in evidence:
        lines.append(f"| `{e['work_item']}` | `{e['evidence_type']}` | {e['reference']} | `{e['result']}` | {e['scope']} | {e['observed_at']} | {e['notes']} |")
    lines += ["","## Comandos","",
        "```bash","python scripts/work_map.py status","python scripts/work_map.py next",
        "python scripts/work_map.py inspect CC-04","python scripts/work_map.py render",
        "python scripts/work_map.py check","```","",
        "Fonte: `data/work_graph.csv`. Evidência: `data/work_evidence.csv`. Projeção tabular: `docs/WORK_STATUS.csv`.",""]
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", nargs="?", default="render", choices=["render","check","status","next","inspect","json"])
    p.add_argument("item", nargs="?")
    a = p.parse_args()
    try:
        model, evidence = build(); by = {x["id"]:x for x in model}
        md, ct = render(model,evidence), csv_text(model)
        if a.command == "render":
            OUT_MD.write_text(md, encoding="utf-8", newline="\n"); OUT_CSV.write_text(ct, encoding="utf-8", newline="")
            print("generated docs/WORK_MAP.md and docs/WORK_STATUS.csv")
        elif a.command == "check":
            ok = OUT_MD.exists() and OUT_CSV.exists() and OUT_MD.read_text(encoding="utf-8") == md and OUT_CSV.read_text(encoding="utf-8-sig") == ct
            print("work map consistent" if ok else "work map stale: run python scripts/work_map.py render")
            return 0 if ok else 1
        elif a.command == "status": print(ct, end="")
        elif a.command == "next":
            print(json.dumps({"verification_debt":[x["id"] for x in model if x["integrated"] and x["tests_defined"] and not x["tests_gated"]],
                              "ready":[x["id"] for x in model if x["state"]=="READY"]}, indent=2))
        elif a.command == "inspect":
            if not a.item or a.item not in by: raise ValueError("inspect requires valid work item id")
            x=by[a.item]; print(json.dumps({"id":x["id"],"title":x["title"],"state":x["state"],"build_dependencies":x["build"],
                "proof_dependencies":x["proof"],"owners":x["owners"],"tests":x["tests"],"system_tests":x["system"],
                "next":action(x,by),"evidence":x["evidence"]}, indent=2, ensure_ascii=False))
        else: print(json.dumps(status(model), indent=2, ensure_ascii=False))
    except (OSError, ValueError, SyntaxError, csv.Error) as e:
        print("work map error:", e); return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
