from __future__ import annotations
import os, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAX_ATTEMPTS=3
TESTS=[
 [sys.executable,"tests/test_discover.py","-v"],
 [sys.executable,"tests/test_planner_runtime.py","-v"],
 [sys.executable,"tests/test_intent.py","-v"],
 [sys.executable,"tests/test_standalone.py","-v"],
 [sys.executable,"-m","unittest","tests.test_ir_compiler","-v"],
 [sys.executable,"-m","unittest","tests.test_b2_b3","-v"],
]

def run_suite():
    logs=[]
    for cmd in TESTS:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        logs.append("$ "+" ".join(cmd)+"\n"+p.stdout+"\n"+p.stderr)
        if p.returncode:
            return False,"\n".join(logs)
    p=subprocess.run([sys.executable,"build_b1.py"],cwd=ROOT,text=True,capture_output=True)
    logs.append(p.stdout+"\n"+p.stderr)
    return p.returncode==0,"\n".join(logs)

def repair(log):
    changes=[]
    # Mechanical repair 1: tests executed as files can lose repository-root imports.
    if "ModuleNotFoundError: No module named 'src'" in log:
        wf=ROOT/".github/workflows/core-ci.yml"
        if wf.exists():
            text=wf.read_text(encoding="utf-8")
            new=re.sub(r"python tests/(test_[\w]+)\.py -v",r"python -m unittest tests.\1 -v",text)
            if new!=text:
                wf.write_text(new,encoding="utf-8"); changes.append(str(wf.relative_to(ROOT)))
    # Mechanical repair 2: Windows SQLite cleanup requires explicit close.
    if "WinError 32" in log and "history.db" in log:
        for path in ROOT.glob("tests/test_*.py"):
            text=path.read_text(encoding="utf-8")
            new=re.sub(
                r'with sqlite3\.connect\(([^\n]+)\) as con:\n(\s+)(self\.assert[^\n]+)',
                r'con = sqlite3.connect(\1)\n\2try:\n\2    \3\n\2finally:\n\2    con.close()',
                text)
            if new!=text:
                path.write_text(new,encoding="utf-8"); changes.append(str(path.relative_to(ROOT)))
    # Do not guess arbitrary code changes. Unknown failures are surfaced.
    return sorted(set(changes))

def main():
    for attempt in range(1,MAX_ATTEMPTS+1):
        ok,log=run_suite()
        Path(ROOT/".autocompiler-ci.log").write_text(log,encoding="utf-8")
        if ok:
            print(f"AUTOCOMPILER_CI_OK attempt={attempt}")
            return 0
        print(f"Attempt {attempt} failed. Trying bounded deterministic repair.",file=sys.stderr)
        changed=repair(log)
        if not changed:
            print("AUTOCOMPILER_CI_NEEDS_REVIEW: no safe deterministic repair matched.",file=sys.stderr)
            print(log[-12000:],file=sys.stderr)
            return 1
        print("Repaired: "+", ".join(changed))
    print("AUTOCOMPILER_CI_NEEDS_REVIEW: repair limit reached.",file=sys.stderr)
    return 1

if __name__=="__main__":
    raise SystemExit(main())
