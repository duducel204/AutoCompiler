from __future__ import annotations
import json, shutil
from pathlib import Path
from src.autocompiler.compiler import compile_ir
from src.autocompiler.ir import load_ir

ROOT = Path(__file__).resolve().parent
ir = load_ir(ROOT / "examples" / "b1-folder-copy.ir.json")
build = ROOT / "generated" / "b1"
if build.exists():
    shutil.rmtree(build)
for target in ("python-sqlite", "python-json"):
    target_ir = json.loads(json.dumps(ir))
    target_ir["state"]["file"] = "history.db" if target == "python-sqlite" else "history.jsonl"
    manifest = compile_ir(target_ir, target, build / target)
    print(json.dumps(manifest, ensure_ascii=False))
print("=== B1 MULTI-TARGET COMPILE: PASS ===")
