"""A scripted, process-free operator for offline runs and tests.

It plays a full, convergent round sequence so the engine, termination, and
report layers can be exercised deterministically:

* ARCHITECT: PROPOSE -> "DRAFT v1"; REVISE -> a stable "FINAL DRAFT" (so round 1
  is a *change* and round 2 is *stable*); SYNTHESIZE -> the final + change log.
* ADVERSARY: round 1 -> objections, ``certify:false``; round >= 2 -> ``certify:
  true`` with no objections. Combined with the stable artifact, this trips the
  consensus gate at round 2 (before ``max_rounds``), proving the
  adversary-driven termination path — not just the round cap.
* LOCAL / FOURTH: short consistency / arbitration notes.
"""
from __future__ import annotations

from ..adapters.base import Phase, Role, Status, TurnRequest, TurnResult, Usage


class FakeAdapter:
    def __init__(self, name: str, role: Role, model: str = "fake") -> None:
        self.name = name
        self.role = role
        self.model_id = model
        self.total_timeout_s = 30.0
        self.calls: list[tuple[int, str]] = []

    async def health_check(self):
        from ..adapters.base import HealthStatus
        return HealthStatus(ok=True, detail="fake adapter", model_id=self.model_id)

    async def invoke(self, turn: TurnRequest) -> TurnResult:
        self.calls.append((turn.round_no, turn.phase.value))
        content = self._script(turn)
        return TurnResult(
            operator_name=self.name,
            role=self.role,
            content=content,
            status=Status.OK,
            usage=Usage(input_tokens=10, output_tokens=20, metered=False, local=(self.role is Role.LOCAL)),
        )

    def _script(self, turn: TurnRequest) -> str:
        r, phase = turn.round_no, turn.phase
        if self.role is Role.ARCHITECT:
            if phase is Phase.PROPOSE:
                return "# DRAFT v1\n\nInitial approach to: " + turn.task
            if phase is Phase.REVISE:
                # Stable across rounds -> unchanged in round 2.
                return "# FINAL DRAFT\n\nHardened approach to: " + turn.task
            if phase is Phase.SYNTHESIZE:
                return (
                    "# FINAL DRAFT\n\nHardened approach to: " + turn.task
                    + "\n\n## Change log\n- addressed placeholder objections from round 1"
                )
        if self.role is Role.ADVERSARY:
            if r >= 2:
                return "No further material objections.\n\n```verdict\n{\"certify\": true, \"objections\": []}\n```"
            return (
                "Objections:\n- unproven assumption A\n- missing failure mode B\n\n"
                "```verdict\n{\"certify\": false, \"objections\": [\"assumption A\", \"failure mode B\"]}\n```"
            )
        if self.role is Role.LOCAL:
            return "Consistency check: no contradictions with earlier turns."
        if self.role is Role.FOURTH:
            if phase is Phase.ARBITRATE:
                return "Decision: side with the adversary on point B; architect must add the failure mode."
            return "Specialist note: consider the resource-exhaustion edge case."
        return f"[{self.role.value}] noted."
