from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from .change_plan import Change, ChangePlan, ApplyEngine
from .environment_manifest import register
from .portable_provider import acquire_verified_file, sha256

def plan_portable_capability(intent: str, capability: str, provider: str, source: str | Path, install_dir: str | Path, consumer: str) -> ChangePlan:
    source=Path(source)
    destination=Path(install_dir)/source.name
    return ChangePlan(intent,[
        Change("acquire",str(destination),f"Provide missing capability {capability}",True,{
            "provider":provider,"capability":capability,"source":str(source),
            "sha256":sha256(source),"consumer":consumer,"strategy":"portable-copy"
        })
    ],{"zero_cost":True,"no_admin":True,"no_recurring_ai":True})

def apply_portable_plan(plan: ChangePlan, manifest_path: str | Path, authorized: bool=False) -> dict:
    def execute(change: Change) -> bool:
        m=change.metadata
        try:
            acquire_verified_file(m["source"],change.target,m["sha256"])
            return True
        except (OSError,ValueError):
            return False
    def verify(change: Change) -> bool:
        return Path(change.target).exists() and sha256(change.target)==change.metadata["sha256"]
    result=ApplyEngine(execute,verify).apply(plan,authorized)
    if result.get("ok"):
        for change in plan.changes:
            m=change.metadata
            register(manifest_path,m["provider"],m["capability"],"autocompiler",m["consumer"])
    return result

def compile_independent_consumer(provider_path: str | Path, output_dir: str | Path) -> Path:
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    provider=str(Path(provider_path).resolve())
    program=out/"automation.py"
    program.write_text(
        "from __future__ import annotations\nimport subprocess, json\n"
        f"PROVIDER={provider!r}\n"
        "p=subprocess.run([PROVIDER],text=True,capture_output=True)\n"
        "print(json.dumps({'ok':p.returncode==0,'provider_output':p.stdout.strip(),"
        "'autocompiler_runtime_used':False,'recurring_ai_used':False}))\n"
        "raise SystemExit(p.returncode)\n",encoding="utf-8")
    return program
