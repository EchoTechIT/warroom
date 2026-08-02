"""Uniform retry/timeout wrapper applied to every adapter call.

Cross-cutting behavior lives here, once, instead of in each adapter:

* **Timeout** — ``asyncio.wait_for`` around the whole turn; breach -> TIMEOUT.
* **Retry** — bounded exponential backoff with jitter, only on *retriable*
  statuses (TIMEOUT/ERROR) and raised transient exceptions. A clean refusal,
  an EMPTY parse, or UNAVAILABLE is surfaced, never hammered.
* **Availability** — UNAVAILABLE is returned as-is; the engine degrades
  gracefully rather than crashing.

Jitter uses a caller-injected sequence (default: deterministic) so runs stay
reproducible and tests are stable — we never call ``random`` in the core path.
"""
from __future__ import annotations

import asyncio
import time
from typing import Callable, Iterator, Optional

from .adapters.base import OperatorAdapter, Status, TurnRequest, TurnResult, Usage


def _zero_jitter() -> Iterator[float]:
    while True:
        yield 0.0


async def invoke_with_policy(
    adapter: OperatorAdapter,
    turn: TurnRequest,
    *,
    total_timeout_s: float,
    max_retries: int = 2,
    base_backoff_s: float = 1.0,
    jitter: Optional[Iterator[float]] = None,
    sleep: Callable[[float], "asyncio.Future"] = asyncio.sleep,
) -> TurnResult:
    jitter = jitter or _zero_jitter()
    attempt = 0
    last: Optional[TurnResult] = None

    while True:
        started = time.monotonic()
        try:
            result = await asyncio.wait_for(adapter.invoke(turn), timeout=total_timeout_s)
        except asyncio.TimeoutError:
            result = TurnResult(
                operator_name=getattr(adapter, "name", "?"),
                role=turn.role,
                content="",
                status=Status.TIMEOUT,
                error=f"turn exceeded {total_timeout_s}s",
            )
        except Exception as exc:  # transient transport failure
            result = TurnResult(
                operator_name=getattr(adapter, "name", "?"),
                role=turn.role,
                content="",
                status=Status.ERROR,
                error=f"{type(exc).__name__}: {exc}",
            )
        if not result.latency_ms:
            result.latency_ms = int((time.monotonic() - started) * 1000)

        last = result
        if result.ok or not result.status.is_retriable or attempt >= max_retries:
            return result

        delay = base_backoff_s * (2 ** attempt) + next(jitter)
        await sleep(delay)
        attempt += 1

    return last  # unreachable
