"""GATE logic — when does a run stop?

Opinionated default: termination is **adversary-driven**, not
architect-satisfied. That is the anti-sycophancy valve — the run ends when the
*critic* certifies "no material objection", which is the harder and more
valuable bar than the author declaring themselves done.

Three conditions, first to fire wins (checked at GATE):

1. **Consensus** — the adversary certifies AND the architect made no substantive
   change this round.
2. **Fixed cap** — ``max_rounds`` reached.
3. **Budget / quorum** — any hard limit hit, or too few operators to form a
   quorum (need architect + >=1 critic).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

# The adversary is asked to emit a machine-readable trailer in a fenced block:
#   ```verdict
#   {"certify": true, "objections": []}
#   ```
_VERDICT_RE = re.compile(r"```verdict\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


@dataclass
class Verdict:
    certify: bool
    objections: list
    raw_found: bool = True


def parse_verdict(adversary_content: str) -> Verdict:
    """Extract the adversary's structured verdict.

    Two hardening rules:

    * The **last** verdict block wins. The adversary is instructed to *end* its
      message with the trailer, so earlier fenced blocks are quoted material —
      the artifact under review, an example in the discussion — and must never
      speak for the reviewer.
    * ``certify`` must be the JSON literal ``true``. Any other value ("false",
      "true", 1) reads as not certified — a type coercion must never
      manufacture consensus.

    Missing or malformed trailer is treated as *not certified* — we never let an
    unparseable review be read as consensus.
    """
    blocks = _VERDICT_RE.findall(adversary_content or "")
    if not blocks:
        return Verdict(certify=False, objections=[], raw_found=False)
    try:
        data = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return Verdict(certify=False, objections=[], raw_found=False)
    return Verdict(
        certify=data.get("certify") is True,
        objections=list(data.get("objections", []) or []),
    )


@dataclass
class GateDecision:
    stop: bool
    reason: str


def decide(
    *,
    round_no: int,
    max_rounds: int,
    adversary_content: Optional[str],
    architect_changed: bool,
    budget_exhausted: bool,
    budget_reason: str,
    quorum_ok: bool,
    require_certify: bool = True,
) -> GateDecision:
    if budget_exhausted:
        return GateDecision(True, f"budget/limit: {budget_reason}")

    if not quorum_ok:
        return GateDecision(True, "quorum lost (need architect + >=1 critic)")

    if require_certify and adversary_content is not None:
        verdict = parse_verdict(adversary_content)
        if verdict.certify and not architect_changed:
            return GateDecision(True, "consensus: adversary certified, artifact stable")

    if round_no >= max_rounds:
        return GateDecision(True, f"max_rounds ({max_rounds}) reached")

    return GateDecision(False, "continue")
