from __future__ import annotations

import json, time
from typing import Any
from urllib.request import Request, urlopen
from .providers import CapabilityProvider

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


class HTTPRequestProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "http.request"

    @property
    def provider_name(self) -> str:
        return "autocompiler.http_provider"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        return request(
            method=params.get("method", "GET"),
            url=params["url"],
            body=params.get("body"),
            retries=int(params.get("retries", 0)),
        )


HTTPClientProvider = HTTPRequestProvider
