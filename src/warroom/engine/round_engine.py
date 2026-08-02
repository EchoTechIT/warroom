"""The deterministic round engine — Warroom's control flow.

    INTAKE
      -> architect PROPOSE (first draft)
    ROUND n (1..max_rounds):
      CRITIQUE   adversary (+ local, + fourth-as-specialist) run concurrently
      REVISE     architect integrates or rebuts -> new draft
      [ARBITRATE] fourth-as-tiebreaker, only on a near-deadlock
      GATE       stop? (adversary-certify | max_rounds | budget/quorum)
    SYNTHESIZE   architect emits final artifact + change log
    EMIT         handled by the caller (see report.py)

No hidden agent recursion: an explicit phase sequence a reviewer can audit.
Operator unavailability is a normal branch, not a crash — a missing critic just
drops out as long as quorum (architect + >=1 critic) holds.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from ..adapters.base import (
    OperatorAdapter,
    Phase,
    Role,
    Status,
    TurnRequest,
    TurnResult,
)
from ..prompts import assemble, instruction_for
from .budget import Budget
from .termination import decide, parse_verdict
from .transcript import Transcript


@dataclass
class RunResult:
    task: str
    final_artifact: str
    transcript: Transcript
    rounds_run: int
    stop_reason: str
    panel_note: str
    budget: dict
    unavailable: List[str] = field(default_factory=list)
    truncated: bool = False


def _norm(s: str) -> str:
    return " ".join((s or "").split())


class RoundEngine:
    def __init__(
        self,
        *,
        panel: Dict[str, OperatorAdapter],
        charters: Dict[Role, str],
        budget: Budget,
        require_certify: bool = True,
        quorum_min: int = 2,
        compaction: Optional[dict] = None,
        invoke: Optional[Callable] = None,
        panel_note: str = "",
    ) -> None:
        self.panel = panel
        self.charters = charters
        self.budget = budget
        self.require_certify = require_certify
        self.quorum_min = quorum_min
        self.compaction = compaction or {}
        self.panel_note = panel_note
        self.transcript = Transcript()
        self.unavailable: set[str] = set()

        # Late import keeps the engine importable without the invoke module's
        # optional deps; the default is the real policy wrapper.
        if invoke is None:
            from ..invoke import invoke_with_policy
            invoke = invoke_with_policy
        self._invoke = invoke

    # -- panel helpers -----------------------------------------------------
    def _by_role(self, role: Role) -> List[OperatorAdapter]:
        return [
            a for a in self.panel.values()
            if a.role is role and a.name not in self.unavailable
        ]

    def _architect(self) -> Optional[OperatorAdapter]:
        got = self._by_role(Role.ARCHITECT)
        return got[0] if got else None

    def _critics(self) -> List[OperatorAdapter]:
        out: List[OperatorAdapter] = []
        out.extend(self._by_role(Role.ADVERSARY))
        out.extend(self._by_role(Role.LOCAL))
        return out

    def _quorum_ok(self) -> bool:
        arch = 1 if self._architect() else 0
        return arch + len(self._critics()) >= self.quorum_min

    # -- a single turn -----------------------------------------------------
    async def _turn(self, adapter: OperatorAdapter, phase: Phase, round_no: int) -> TurnResult:
        await self._maybe_compact()
        charter = self.charters.get(adapter.role, f"You are the {adapter.role.value}.")
        req = TurnRequest(
            role=adapter.role,
            system_prompt=charter,
            task=self.task,
            transcript=self.transcript.marshal_for(adapter.role),
            round_no=round_no,
            phase=phase,
            phase_instruction=instruction_for(adapter.role, phase),
            budget_hint=self._budget_hint(round_no),
        )
        # The adapter's own prompt assembly happens inside it, but we hand it a
        # fully assembled prompt via system+instruction for transports (CLI) that
        # take a single string; HTTP adapters use the structured fields.
        req_prompt = assemble(
            charter=charter,
            task=self.task,
            transcript=req.transcript,
            instruction=req.phase_instruction,
            budget_hint=req.budget_hint,
        )
        # Stash the assembled single-string prompt for CLI adapters.
        setattr(req, "assembled_prompt", req_prompt)

        timeout = getattr(adapter, "total_timeout_s", 300.0)
        result = await self._invoke(adapter, req, total_timeout_s=timeout)

        self.budget.record(result.usage)
        if result.status is Status.UNAVAILABLE:
            self.unavailable.add(adapter.name)
        if result.ok:
            self.transcript.append(result, round_no, phase)
        return result

    def _budget_hint(self, round_no: int) -> str:
        return (
            f"round {round_no}/{self.budget.max_rounds}; "
            f"~{round(self.budget.elapsed_s(), 0)}s elapsed; "
            f"${self.budget.spent_usd:.2f} spent"
        )

    async def _maybe_compact(self) -> None:
        if not self.compaction:
            return
        frac = self.compaction.get("trigger_fraction", 0.6)
        cap = self.budget.per_turn_token_cap
        if not self.transcript.needs_compaction(Role.LOCAL, cap, frac):
            return
        summarizer = self._compaction_summarizer()
        if summarizer is None:
            return  # no free local model available; leave the transcript intact
        self.transcript.compact(summarizer)

    def _compaction_summarizer(self):
        locals_ = self._by_role(Role.LOCAL)
        if not locals_:
            return None
        adapter = locals_[0]

        def summarize(text: str) -> str:
            # Synchronous shim: compaction runs a quick, bounded local call.
            req = TurnRequest(
                role=Role.LOCAL,
                system_prompt="Summarize the discussion faithfully and compactly.",
                task=self.task,
                transcript="",
                round_no=0,
                phase=Phase.INTAKE,
                phase_instruction="Summarize the following discussion in <=200 words:\n\n" + text,
            )
            try:
                res = asyncio.get_event_loop().run_until_complete(adapter.invoke(req))
                return res.content if res.ok else "[summary unavailable]"
            except RuntimeError:
                # Already inside a running loop; skip rather than deadlock.
                return "[summary skipped: nested loop]"

        return summarize

    # -- the run -----------------------------------------------------------
    async def run(self, task: str) -> RunResult:
        self.task = task

        architect = self._architect()
        if architect is None:
            raise RuntimeError("no architect available at INTAKE")

        # PROPOSE — first draft.
        draft = await self._turn(architect, Phase.PROPOSE, round_no=1)
        if draft.ok:
            self.transcript.set_artifact(draft.content)

        stop_reason = "not started"
        rounds_run = 0
        truncated = False

        round_no = 1
        while True:
            rounds_run = round_no

            # CRITIQUE — critics concurrently.
            critics = self._critics()
            critic_results = await asyncio.gather(
                *[self._turn(c, Phase.CRITIQUE, round_no) for c in critics]
            ) if critics else []
            adversary_content = next(
                (r.content for r in critic_results if r.role is Role.ADVERSARY and r.ok),
                None,
            )

            # REVISE — architect integrates.
            before = _norm(self.transcript.current_artifact)
            architect = self._architect()
            if architect is not None:
                revised = await self._turn(architect, Phase.REVISE, round_no)
                if revised.ok:
                    self.transcript.set_artifact(revised.content)
            after = _norm(self.transcript.current_artifact)
            architect_changed = before != after

            # ARBITRATE — fourth-as-tiebreaker, only near deadlock.
            await self._maybe_arbitrate(round_no, adversary_content, architect_changed)

            # GATE.
            exhausted = self.budget.exhausted(round_no)
            decision = decide(
                round_no=round_no,
                max_rounds=self.budget.max_rounds,
                adversary_content=adversary_content,
                architect_changed=architect_changed,
                budget_exhausted=exhausted,
                budget_reason="; ".join(self.budget.reasons[-1:]) or "limit",
                quorum_ok=self._quorum_ok(),
                require_certify=self.require_certify,
            )
            if decision.stop:
                stop_reason = decision.reason
                truncated = exhausted and "consensus" not in decision.reason
                break

            round_no += 1

        # SYNTHESIZE — final artifact + change log.
        architect = self._architect()
        final = self.transcript.current_artifact
        if architect is not None:
            synth = await self._turn(architect, Phase.SYNTHESIZE, rounds_run)
            if synth.ok:
                final = synth.content
                self.transcript.set_artifact(final)

        return RunResult(
            task=task,
            final_artifact=final,
            transcript=self.transcript,
            rounds_run=rounds_run,
            stop_reason=stop_reason,
            panel_note=self.panel_note,
            budget=self.budget.summary(),
            unavailable=sorted(self.unavailable),
            truncated=truncated,
        )

    async def _maybe_arbitrate(self, round_no: int, adversary_content: Optional[str], architect_changed: bool) -> None:
        fourth = self._by_role(Role.FOURTH)
        if not fourth:
            return
        # Only arbitrate on a near-deadlock: last planned round, still churning,
        # and the adversary has not certified.
        near_end = round_no >= self.budget.max_rounds - 1
        certified = adversary_content is not None and parse_verdict(adversary_content).certify
        if near_end and architect_changed and not certified:
            await self._turn(fourth[0], Phase.ARBITRATE, round_no)
