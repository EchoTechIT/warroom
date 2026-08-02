"""The transcript — Warroom's single source of truth and shared memory.

Operators share no memory with one another, so the orchestrator *is* the memory:
every turn is appended here, and every operator's prompt is rebuilt from this
record. Stored canonically as JSONL; rendered to each operator as *attributed*
markdown (who said what matters — the architect must weigh authority).

Compaction only ever summarizes older *discussion*. The current artifact is
always passed verbatim; it is never summarized away.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from ..adapters.base import Phase, Role, TurnResult


@dataclass
class Turn:
    round_no: int
    phase: str
    operator: str
    role: str
    content: str
    #: Injected monotonic sequence — we avoid wall-clock so runs are
    #: reproducible; a real timestamp is stamped by the report layer.
    seq: int = 0
    #: True once this turn's discussion has been folded into a summary.
    summarized: bool = False


class Transcript:
    def __init__(self) -> None:
        self._turns: List[Turn] = []
        self._seq = 0
        #: The current artifact draft (owned by the architect), kept out of band
        #: so compaction can never touch it.
        self.current_artifact: str = ""

    # -- writing -----------------------------------------------------------
    def append(self, result: TurnResult, round_no: int, phase: Phase) -> Turn:
        self._seq += 1
        turn = Turn(
            round_no=round_no,
            phase=phase.value,
            operator=result.operator_name,
            role=result.role.value,
            content=result.content,
            seq=self._seq,
        )
        self._turns.append(turn)
        return turn

    def set_artifact(self, content: str) -> None:
        self.current_artifact = content

    @property
    def turns(self) -> List[Turn]:
        return list(self._turns)

    # -- reading / marshaling ---------------------------------------------
    def marshal_for(self, role: Role) -> str:
        """Render the transcript for an operator's prompt as attributed markdown.

        The current artifact is always included in full, followed by the
        (possibly compacted) discussion. ``role`` is accepted for future
        role-specific views; today every operator sees the same marshaled view.
        """
        blocks: List[str] = []
        if self.current_artifact.strip():
            blocks.append("## CURRENT ARTIFACT (verbatim)\n\n" + self.current_artifact.strip())

        if self._turns:
            blocks.append("## DISCUSSION")
            for t in self._turns:
                tag = "summary" if t.summarized else "turn"
                header = (
                    f"### ROUND {t.round_no} · {t.role.upper()} "
                    f"({t.operator}) · {t.phase} [{tag}]"
                )
                blocks.append(f"{header}\n\n{t.content.strip()}")

        return "\n\n".join(blocks).strip()

    def approx_tokens(self, role: Role) -> int:
        """Cheap heuristic: ~4 chars/token. Exact counting lives in budget.py
        for metered operators; this is only for compaction triggering."""
        return len(self.marshal_for(role)) // 4

    # -- compaction --------------------------------------------------------
    def needs_compaction(self, role: Role, per_turn_token_cap: int, trigger_fraction: float) -> bool:
        return self.approx_tokens(role) > per_turn_token_cap * trigger_fraction

    def compact(self, summarize: Callable[[str], str], keep_recent_rounds: int = 1) -> None:
        """Fold discussion older than the most recent ``keep_recent_rounds`` into
        a single labeled summary turn. ``summarize`` is supplied by the caller
        (the free local operator, per policy). Never touches the artifact.
        """
        if not self._turns:
            return
        latest_round = max(t.round_no for t in self._turns)
        cutoff = latest_round - keep_recent_rounds
        old = [t for t in self._turns if t.round_no <= cutoff and not t.summarized]
        if len(old) < 2:
            return  # not worth summarizing a single turn

        rendered = "\n\n".join(
            f"[{t.role.upper()} r{t.round_no}] {t.content}" for t in old
        )
        summary_text = summarize(rendered)
        kept = [t for t in self._turns if t not in old]
        summary_turn = Turn(
            round_no=cutoff,
            phase="compaction",
            operator="local",
            role=Role.LOCAL.value,
            content=summary_text,
            seq=old[0].seq,
            summarized=True,
        )
        self._turns = [summary_turn] + kept
        self._turns.sort(key=lambda t: t.seq)

    # -- persistence -------------------------------------------------------
    def write_jsonl(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for t in self._turns:
                fh.write(json.dumps(asdict(t), ensure_ascii=False) + "\n")

    @classmethod
    def read_jsonl(cls, path: str | Path) -> "Transcript":
        t = cls()
        with Path(path).open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                t._turns.append(Turn(**json.loads(line)))
        t._seq = max((x.seq for x in t._turns), default=0)
        return t
