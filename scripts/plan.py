import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover
from autocompiler.planner import Requirement, plan

intent = " ".join(sys.argv[1:]).strip() or "Run a local scheduled Python automation with durable state."
requirements = [Requirement("run_python"), Requirement("schedule"), Requirement("state")]
result = plan(intent, requirements, discover())
print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
