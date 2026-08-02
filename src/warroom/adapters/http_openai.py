"""HTTP OpenAI-compatible adapter — serves BOTH local Ollama and cloud APIs.

Ollama and any cloud OpenAI-compatible endpoint (DeepSeek, etc.) differ only by
``base_url``, ``api_key``, ``model``, and price table, so one class covers both.
Ollama needs no auth (tailnet-only) and is unmetered; a cloud endpoint is
metered and its cost is computed from the price table.

STATUS: ``invoke`` is a **stub**; ``health_check`` is real (pings ``/models``).
Real streaming chat-completions is the ``# TODO(real)`` below.
"""
from __future__ import annotations

import os
from typing import Optional

from ..config.models import HttpConfig
from .base import (
    HealthStatus,
    OperatorAdapter,
    Role,
    Status,
    TurnRequest,
    TurnResult,
    Usage,
)


class HttpOpenAIAdapter(OperatorAdapter):
    def __init__(self, name: str, role: Role, model: str, http: HttpConfig) -> None:
        self.name = name
        self.role = role
        self.model_id = model
        self.http = http
        self.total_timeout_s = http.total_timeout_s

    def _api_key(self) -> Optional[str]:
        if not self.http.api_key_env:
            return None
        return os.environ.get(self.http.api_key_env)

    def _cost(self, usage: Usage) -> float:
        if not (self.http.metered and self.http.price_per_mtok):
            return 0.0
        p = self.http.price_per_mtok
        return (usage.input_tokens * p.input + usage.output_tokens * p.output) / 1_000_000

    async def health_check(self) -> HealthStatus:
        try:
            import httpx  # lazy: keep engine importable without httpx
        except ImportError:
            return HealthStatus(ok=False, detail="httpx not installed")

        url = self.http.base_url.rstrip("/") + "/models"
        headers = {}
        key = self._api_key()
        if self.http.api_key_env and not key:
            return HealthStatus(ok=False, detail=f"{self.http.api_key_env} not set in env")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
            if resp.status_code >= 400:
                return HealthStatus(ok=False, detail=f"{url} -> HTTP {resp.status_code}")
            return HealthStatus(ok=True, detail=f"{url} reachable", model_id=self.model_id)
        except Exception as exc:
            return HealthStatus(ok=False, detail=f"{type(exc).__name__}: {exc}")

    async def invoke(self, turn: TurnRequest) -> TurnResult:
        # TODO(real): POST {base_url}/chat/completions with messages=
        #   [{"role":"system","content":turn.system_prompt},
        #    {"role":"user","content":assembled}], stream=True; sum usage;
        #   cost = self._cost(usage). Map 429/5xx -> UNAVAILABLE/ERROR.
        tag = "local" if self.http.local else "cloud"
        canned = (
            f"## {self.role.value.title()} note (stub: HttpOpenAIAdapter/{tag})\n\n"
            f"- Consistency check: draft is internally consistent so far.\n"
            f"- No contradictions with earlier turns detected."
        )
        usage = Usage(metered=self.http.metered, local=self.http.local,
                      input_tokens=0, output_tokens=0)
        usage.cost_usd = self._cost(usage)
        return TurnResult(self.name, self.role, canned, status=Status.OK, usage=usage)
