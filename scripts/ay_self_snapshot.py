"""Emit a compact deterministic snapshot of AY's current operational state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from autocompiler.ay.state import build_ay_state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", default="", help="Current intent used only to label the snapshot")
    args = parser.parse_args()

    state = build_ay_state(intent=args.intent)
    print(json.dumps(state.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
