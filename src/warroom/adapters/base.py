"""The operator-adapter contract.

This is the single seam every operator crosses, regardless of transport. Two
adapter families implement it:

* CLI-shell adapters (Claude Code, Codex) — subprocess, prompt via stdin.
* HTTP OpenAI-compatible adapters (Ollama, cloud APIs) — one class, differ only
  by ``base_url``/``api_key``/``model``.

The contract is deliberately **stateless**: every field an operator needs to
answer a turn is passed in on ``TurnRequest``, because the subscription CLIs and
the local model share no memory with each other. The orchestrator *is* the
memory (see ``warroom.engine.transcript``).

Kept to the standard library on purpose so the engine and its tests never need
the provider SDKs installed.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol, runtime_checkable


class Role(enum.Enum):
    """The four seats at the table. Role drives prompt framing and authority."""

    ARCHITECT = "architect"
    ADVERSARY = "adversary"
    LOCAL = "local"
    FOURTH = "fourth"


class Phase(enum.Enum):
    """Phases of a run. See ``warroom.engine.phases`` for the dispatch table."""

    INTAKE = "intake"
    PROPOSE = "propose"
    CRITIQUE = "critique"
    ARBITRATE = "arbitrate"
    REVISE = "revise"
    GATE = "gate"
    SYNTHESIZE = "synthesize"
    EMIT = "emit"


class Status(enum.Enum):
    """Normalized outcome of an ``invoke`` across every transport."""

    OK = "ok"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"  # rate-capped / not logged in / endpoint down
    ERROR = "error"
    EMPTY = "empty"  # returned nothing / unparseable — treated as a soft failure

    @property
    def is_ok(self) -> bool:
        return self is Status.OK

    @property
    def is_retriable(self) -> bool:
        # A dead seat or a transient error is worth a bounded retry; a clean
        # refusal or an empty parse is not (retrying just burns the seat).
        return self in (Status.TIMEOUT, Status.ERROR)


@dataclass
class Usage:
    """Token/cost accounting. Asymmetric by design — see ``metered``."""

    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    #: Flat-rate subscription seats and local Ollama are *unmetered* (cost is 0
    #: no matter the token count); only cloud-API operators are metered. Budgets
    #: gate metered operators by dollars and everyone by wall-clock/rounds.
    metered: bool = False
    #: True for on-GPU models — no dollars, but real GPU time.
    local: bool = False


@dataclass
class HealthStatus:
    ok: bool
    detail: str = ""
    #: Live model id reported by the backend, when discoverable — the tripwire
    #: for silent model-version drift.
    model_id: Optional[str] = None


@dataclass
class TurnRequest:
    """Everything an operator needs to answer one turn. Identical shape for
    every adapter."""

    role: Role
    system_prompt: str
    task: str
    #: Marshaled prior turns, already rendered to attributed markdown by the
    #: transcript layer.
    transcript: str
    round_no: int
    phase: Phase
    #: Free-text instruction for *this* phase (what to actually do now).
    phase_instruction: str
    #: Soft hint of remaining budget, for the operator to self-pace.
    budget_hint: str = ""


@dataclass
class TurnResult:
    """Normalized result of a turn across every transport."""

    operator_name: str
    role: Role
    content: str
    status: Status = Status.OK
    usage: Usage = field(default_factory=Usage)
    latency_ms: int = 0
    #: Provider-native blob for debugging; never fed back into a prompt.
    raw: Any = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status.is_ok and bool(self.content.strip())


@runtime_checkable
class OperatorAdapter(Protocol):
    """The one interface the engine talks to."""

    name: str
    role: Role
    model_id: str

    async def health_check(self) -> HealthStatus: ...

    async def invoke(self, turn: TurnRequest) -> TurnResult: ...
