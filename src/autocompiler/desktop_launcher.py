from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def _reachable() -> bool:
    try:
        with urllib.request.urlopen(URL + "/api/templates", timeout=0.5) as response:
            return response.status == 200
    except Exception:
        return False


def _install_root() -> Path:
    explicit = os.environ.get("AUTOCOMPILER_HOME")
    if explicit:
        return Path(explicit).expanduser().resolve()
    runtime = Path(sys.executable).resolve().parent
    return runtime.parent


def launch() -> int:
    root = _install_root()
    app = root / "app"
    state = root / "state"
    generated = root / "generated"
    state.mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["AUTOCOMPILER_HOME"] = str(root)
    env["AUTOCOMPILER_STATE_ROOT"] = str(state)
    env["AUTOCOMPILER_GENERATED_ROOT"] = str(generated)

    if not _reachable():
        pythonw = root / "runtime" / "pythonw.exe"
        python = pythonw if pythonw.exists() else root / "runtime" / "python.exe"
        subprocess.Popen(
            [str(python), "-m", "autocompiler.local_canvas"],
            cwd=str(app),
            env=env,
            close_fds=True,
        )

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if _reachable():
                break
            time.sleep(0.25)

    if not _reachable():
        raise RuntimeError(f"AutoCompiler Canvas did not become reachable at {URL}")

    webbrowser.open(URL)
    return 0


if __name__ == "__main__":
    raise SystemExit(launch())
