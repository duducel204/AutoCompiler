from __future__ import annotations

import json, time
from urllib.request import Request, urlopen

def request(method: str, url: str, body=None, retries: int = 0):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data else {}
    last = None
    for attempt in range(retries + 1):
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method.upper()), timeout=15) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {"status": response.status}
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(min(2 ** attempt, 4))
    raise last
