from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.catalog import CapabilityCatalog
from autocompiler.vault_provider import ObsidianVaultProvider


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify and register an Obsidian vault as reusable AutoCompiler capabilities."
    )
    parser.add_argument("vault", type=Path)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / ".autocompiler" / "capabilities.json",
    )
    args = parser.parse_args()

    provider = ObsidianVaultProvider(args.vault)
    evidence = provider.verify()
    if (
        not evidence.get("ok")
        or not evidence.get("write_reread")
        or not evidence.get("search_proof")
        or not evidence.get("path_escape_blocked")
    ):
        raise SystemExit("Vault verification failed")

    catalog = CapabilityCatalog(args.catalog)
    evidence_id = (
        "local:vault-contract:"
        f"write-reread={str(evidence['write_reread']).lower()};"
        f"search-proof={str(evidence['search_proof']).lower()};"
        f"path-escape-blocked={str(evidence['path_escape_blocked']).lower()}"
    )

    for contract in provider.capabilities():
        catalog.register_candidate(
            contract.capability,
            contract.provider,
            contract.version,
            ("tests/test_vault_provider.py",),
            permissions=contract.permissions,
            rollback="remove local capability registration; no vault content is owned",
            binding={"root": str(provider.root)},
        )
        catalog.promote(
            contract.capability,
            contract.provider,
            (evidence_id,),
        )

    result = {
        "status": "validated",
        "provider": "obsidian-local-vault",
        "vault_root": str(provider.root),
        "capabilities": list(evidence["capabilities"]),
        "catalog": str(args.catalog),
        "evidence": evidence_id,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
