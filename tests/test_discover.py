import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover


def test_discovery_has_stable_shape():
    result = discover()
    assert result["schema_version"] == "0.1"
    assert result["experiment"] == "E-003"
    assert result["summary"]["checked"] == len(result["capabilities"])
    assert any(c["id"] == "filesystem" and c["available"] for c in result["capabilities"])
    assert any(c["id"] == "sqlite" and c["available"] for c in result["capabilities"])
