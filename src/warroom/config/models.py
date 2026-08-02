"""Pydantic schemas for ``operators.yaml`` and ``warroom.yaml``.

Validation is strict and fail-loud: a bad panel or run policy raises at startup,
never mid-round. The 4th-slot ``variant`` indirection is resolved by the loader
(``loader.resolve_fourth``) so the engine only ever sees plain operators.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..adapters.base import Role

AdapterName = Literal["cli_claude_code", "cli_codex", "http_openai", "fake"]


class StrictModel(BaseModel):
    """Config base: unknown keys are a hard error.

    "Strict and fail-loud" has to be enforced, not asserted — with pydantic's
    default (ignore extras), a typo like ``max_rouds: 1`` would silently fall
    back to the default budget and the run would use limits the user never set.
    """

    model_config = ConfigDict(extra="forbid")


class CliConfig(StrictModel):
    command: List[str] = Field(..., min_length=1)
    base_args: List[str] = Field(default_factory=list)
    prompt_via: Literal["stdin", "arg"] = "stdin"
    workdir: Literal["scratch", "cwd"] = "scratch"
    sandbox: Optional[str] = None  # e.g. "read-only" for a pure reviewer
    first_token_timeout_s: float = 30.0
    total_timeout_s: float = 300.0


class PriceTable(StrictModel):
    input: float = 0.0   # USD per million input tokens
    output: float = 0.0  # USD per million output tokens


class HttpConfig(StrictModel):
    base_url: str
    api_key_env: Optional[str] = None  # None => no auth (Ollama on a tailnet)
    metered: bool = False
    local: bool = False
    price_per_mtok: Optional[PriceTable] = None
    total_timeout_s: float = 300.0

    @model_validator(mode="after")
    def _metered_needs_price(self) -> "HttpConfig":
        if self.metered:
            p = self.price_per_mtok
            if p is None or (p.input <= 0 and p.output <= 0):
                raise ValueError(
                    "metered operator requires a non-zero price_per_mtok — an "
                    "all-zero price table would never trip the dollar gate"
                )
        return self


class OperatorConfig(StrictModel):
    role: Role
    enabled: bool = True
    adapter: AdapterName
    model: str
    charter: Optional[str] = None
    cli: Optional[CliConfig] = None
    http: Optional[HttpConfig] = None

    @model_validator(mode="after")
    def _transport_matches_adapter(self) -> "OperatorConfig":
        cli_adapters = {"cli_claude_code", "cli_codex"}
        if self.adapter in cli_adapters and self.cli is None:
            raise ValueError(f"adapter {self.adapter!r} requires a `cli:` block")
        if self.adapter == "http_openai" and self.http is None:
            raise ValueError("adapter 'http_openai' requires an `http:` block")
        return self


class FourthConfig(StrictModel):
    """The pluggable fourth seat. Two dials: ``enabled`` (on the panel at all)
    and ``variant`` (which backing it uses)."""

    role: Role = Role.FOURTH
    enabled: bool = False
    mode: Literal["tiebreaker", "specialist", "off"] = "tiebreaker"
    variant: Literal["cloud_api", "second_gpu"] = "cloud_api"
    variants: Dict[str, OperatorConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _variant_present_when_enabled(self) -> "FourthConfig":
        if self.enabled and self.mode != "off" and self.variant not in self.variants:
            raise ValueError(
                f"fourth.variant {self.variant!r} not found in fourth.variants"
            )
        return self


class OperatorsFile(StrictModel):
    version: int = 1
    operators: Dict[str, OperatorConfig]
    fourth: FourthConfig = Field(default_factory=FourthConfig)

    @model_validator(mode="after")
    def _need_an_architect(self) -> "OperatorsFile":
        roles = {op.role for op in self.operators.values() if op.enabled}
        if Role.ARCHITECT not in roles:
            raise ValueError("panel must include an enabled ARCHITECT operator")
        return self


class CompactionConfig(StrictModel):
    trigger_fraction: float = 0.6  # of per_turn_token_cap
    summarizer: str = "local"       # operator key used to compact old discussion


class RunConfig(StrictModel):
    max_rounds: int = 3
    max_wall_clock_s: float = 1800.0
    max_cost_usd: float = 2.00       # gates metered operators only
    per_turn_token_cap: int = 24000
    quorum_min_operators: int = 2    # architect + >=1 critic
    compaction: CompactionConfig = Field(default_factory=CompactionConfig)


class TerminationConfig(StrictModel):
    consensus_requires_adversary_certify: bool = True


class OutputConfig(StrictModel):
    dir: str = "runs/{timestamp}-{slug}"
    artifacts: List[str] = Field(
        default_factory=lambda: ["transcript.jsonl", "final_artifact.md", "run_report.md"]
    )


class WarroomFile(StrictModel):
    run: RunConfig = Field(default_factory=RunConfig)
    termination: TerminationConfig = Field(default_factory=TerminationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
