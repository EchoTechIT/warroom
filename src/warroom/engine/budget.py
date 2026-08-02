"""Budget accounting.

The scarce resource is asymmetric, so the accounting is too:

* **Metered** operators (cloud API) are gated by **dollars** (``max_cost_usd``).
* **Seats and local Ollama** are unmetered — gated by **wall-clock** and
  **round count**, because their real limit is subscription rate caps and GPU
  time, not money.

Budget exhaustion is a *clean* terminal state: the engine jumps to SYNTHESIZE
with whatever is current, flagged ``budget-truncated``.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from ..adapters.base import Usage


@dataclass
class Budget:
    max_rounds: int
    max_wall_clock_s: float
    max_cost_usd: float
    per_turn_token_cap: int
    #: Monotonic start; injected so the engine controls the clock (testable).
    started_at: float = field(default_factory=time.monotonic)

    spent_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    reasons: List[str] = field(default_factory=list)

    def record(self, usage: Usage) -> None:
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        if usage.metered:
            self.spent_usd += usage.cost_usd

    def elapsed_s(self, now: float | None = None) -> float:
        return (now if now is not None else time.monotonic()) - self.started_at

    def exhausted(self, round_no: int, now: float | None = None) -> bool:
        if round_no > self.max_rounds:
            self.reasons.append(f"max_rounds ({self.max_rounds}) reached")
            return True
        if self.elapsed_s(now) > self.max_wall_clock_s:
            self.reasons.append(f"wall-clock ({self.max_wall_clock_s}s) exceeded")
            return True
        if self.spent_usd > self.max_cost_usd:
            self.reasons.append(
                f"cost budget (${self.max_cost_usd:.2f}) exceeded at ${self.spent_usd:.2f}"
            )
            return True
        return False

    def summary(self) -> dict:
        return {
            "spent_usd": round(self.spent_usd, 4),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "elapsed_s": round(self.elapsed_s(), 1),
            "reasons": list(self.reasons),
        }
