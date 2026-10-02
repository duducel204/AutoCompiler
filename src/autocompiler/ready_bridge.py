from __future__ import annotations

import ctypes
import json
import os
import struct
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any


HOST_NAME = "com.autocompiler.ready_bridge"
MAX_TEXT_CHARS = 200_000
POWERSHELL_WINDOW_PROCESSES = {
    "powershell.exe",
    "pwsh.exe",
    "windowsterminal.exe",
}


def _read_exact(stream, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = stream.read(size - len(data))
        if not chunk:
            raise EOFError
        data += chunk
    return data


def read_native_message(stream=None) -> dict[str, Any]:
    stream = stream or sys.stdin.buffer
    header = stream.read(4)
    if not header:
        raise EOFError
    if len(header) != 4:
        raise ValueError("invalid native-message header")
    size = struct.unpack("=I", header)[0]
    payload = _read_exact(stream, size)
    return json.loads(payload.decode("utf-8"))


def write_native_message(message: dict[str, Any], stream=None) -> None:
    stream = stream or sys.stdout.buffer
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    stream.write(struct.pack("=I", len(payload)))
    stream.write(payload)
    stream.flush()


def _set_clipboard_text_windows(text: str) -> None:
    if os.name != "nt":
        raise RuntimeError("clipboard bridge is Windows-only")

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    GMEM_MOVEABLE = 0x0002
    CF_UNICODETEXT = 13

    if not user32.OpenClipboard(None):
        raise OSError("OpenClipboard failed")
    handle = None
    try:
        if not user32.EmptyClipboard():
            raise OSError("EmptyClipboard failed")
        raw = (text + "\0").encode("utf-16-le")
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(raw))
        if not handle:
            raise MemoryError("GlobalAlloc failed")
        locked = kernel32.GlobalLock(handle)
        if not locked:
            raise MemoryError("GlobalLock failed")
        try:
            ctypes.memmove(locked, raw, len(raw))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise OSError("SetClipboardData failed")
        handle = None  # ownership transferred to the system
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def _window_process_name(hwnd: int) -> str | None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return None

    process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not process:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            return None
        return Path(buffer.value).name.lower()
    finally:
        kernel32.CloseHandle(process)


def find_powershell_window() -> int | None:
    if os.name != "nt":
        return None
    user32 = ctypes.windll.user32

    foreground = user32.GetForegroundWindow()
    if foreground and _window_process_name(foreground) in POWERSHELL_WINDOW_PROCESSES:
        return int(foreground)

    found: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            name = _window_process_name(hwnd)
            if name in POWERSHELL_WINDOW_PROCESSES:
                found.append(int(hwnd))
        return True

    user32.EnumWindows(callback, 0)
    return found[0] if found else None


def paste_clipboard_without_enter(hwnd: int) -> bool:
    if os.name != "nt":
        return False
    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002

    if not user32.SetForegroundWindow(hwnd):
        return False
    time.sleep(0.12)

    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    return True


def transfer_to_powershell(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text:
        return {"ok": False, "status": "empty_text"}
    if len(text) > MAX_TEXT_CHARS:
        return {"ok": False, "status": "text_too_large", "limit": MAX_TEXT_CHARS}

    _set_clipboard_text_windows(text)
    hwnd = find_powershell_window()
    if hwnd is None:
        return {
            "ok": True,
            "status": "clipboard_only",
            "executed": False,
            "message": "No PowerShell/Windows Terminal window was found. Text is on the clipboard.",
        }

    pasted = paste_clipboard_without_enter(hwnd)
    return {
        "ok": pasted,
        "status": "pasted" if pasted else "clipboard_only",
        "executed": False,
        "window": hwnd,
    }


def handle(message: dict[str, Any]) -> dict[str, Any]:
    action = message.get("action")
    if action != "paste_to_powershell":
        return {"ok": False, "status": "unsupported_action", "action": action}
    try:
        result = transfer_to_powershell(message.get("text", ""))
        return {"host": HOST_NAME, **result}
    except Exception as exc:
        return {
            "host": HOST_NAME,
            "ok": False,
            "status": "bridge_error",
            "executed": False,
            "error": str(exc),
        }


def main() -> int:
    try:
        message = read_native_message()
    except EOFError:
        return 0
    except Exception as exc:
        write_native_message({"host": HOST_NAME, "ok": False, "status": "invalid_message", "error": str(exc)})
        return 1

    write_native_message(handle(message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
