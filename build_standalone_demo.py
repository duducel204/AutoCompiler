from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
from autocompiler.standalone import compile_folder_watch

source = Path.home() / "Desktop" / "AutoCompiler-Inbox"
destination = Path.home() / "Desktop" / "AutoCompiler-Processados"
out = ROOT / "generated" / "folder-automation"
config=compile_folder_watch(str(source),str(destination),out)
print(json.dumps({"ok":True,"generated":str(out),"config":config},indent=2,ensure_ascii=False))
print("\n=== STANDALONE COMPILE: PASS ===")
