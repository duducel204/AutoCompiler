import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.runtime import load_and_execute

if len(sys.argv) != 2:
    raise SystemExit("usage: python scripts/run_recipe.py <recipe.json>")
print(json.dumps(load_and_execute(sys.argv[1]), indent=2, ensure_ascii=False))
