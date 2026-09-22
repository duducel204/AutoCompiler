from __future__ import annotations
import hashlib, shutil
from pathlib import Path

def sha256(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):
            h.update(chunk)
    return h.hexdigest()

def acquire_verified_file(source: str | Path, destination: str | Path, expected_sha256: str) -> Path:
    source,destination=Path(source),Path(destination)
    if sha256(source) != expected_sha256:
        raise ValueError("source checksum mismatch")
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
    if sha256(destination) != expected_sha256:
        destination.unlink(missing_ok=True)
        raise ValueError("installed checksum mismatch")
    return destination

def remove_owned_file(path: str | Path) -> None:
    Path(path).unlink(missing_ok=True)
