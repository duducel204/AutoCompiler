from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DATA = ROOT / "data"

ICONS = {
    "implemented": "DONE",
    "confirmed": "CONFIRMED",
    "leading": "LEADING",
    "active": "ACTIVE",
    "planned": "PLANNED",
    "explore": "EXPLORE",
    "observed": "OBSERVED",
    "deprioritized": "DEPRIORITIZED",
}


def esc(value: str) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def rows(name: str):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stat(value: str) -> str:
    v = esc(value)
    return f"{ICONS.get(v.lower(), 'OPEN')}: {v}"


def table(headers, body):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(esc(x) for x in row) + " |" for row in body]
    return "\n".join(out)


def discoveries():
    return table(
        ["ID", "Type", "Discovery / hypothesis", "Status", "Impact"],
        [[r["id"], r["type"], r["statement"], stat(r["status"]), r["impact"]] for r in rows("discoveries.csv")],
    )


def resources():
    return table(
        ["Resource", "Category", "Local", "Cloud", "Cost", "Execute", "Store", "Trigger"],
        [[r["resource"], r["category"], r["local"], r["cloud"], r["cost_profile"], r["execute"], r["store"], r["trigger"]] for r in rows("resources.csv")],
    )


def hypotheses():
    return table(
        ["ID", "Hypothesis", "Status", "Dependency", "Cost", "Complexity", "Differentiation"],
        [[r["id"], r["hypothesis"], stat(r["status"]), r["dependency"], r["cost"], r["complexity"], r["differentiation"]] for r in rows("hypotheses.csv")],
    )


def roadmap():
    data = rows("roadmap.csv")
    body = [[r["id"], r["phase"], r["experiment"], stat(r["status"]), r["priority"], f'{r["complexity"]}/10', r["question"]] for r in data]
    done = sum(r["status"].lower() == "implemented" for r in data)
    return table(["ID", "Phase", "Experiment", "Status", "Priority", "Complexity", "Question"], body) + f"\n\n**Experiments tracked:** {len(data)} · **Implemented:** {done}"


def replace(text: str, key: str, generated: str) -> str:
    start = f"<!-- {key}_TABLE_START -->"
    end = f"<!-- {key}_TABLE_END -->"
    if start not in text or end not in text:
        raise SystemExit(f"README markers not found for {key}")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return before + start + "\n" + generated + "\n" + end + after


def main():
    text = README.read_text(encoding="utf-8")
    for key, fn in {
        "DISCOVERIES": discoveries,
        "RESOURCES": resources,
        "HYPOTHESES": hypotheses,
        "ROADMAP": roadmap,
    }.items():
        text = replace(text, key, fn())
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
