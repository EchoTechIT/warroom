"""Phase ordering for a round.

A run is: ``INTAKE`` then N rounds of the round-phase sequence below, then
``SYNTHESIZE`` and ``EMIT``. ARBITRATE is conditional — invoked only when the
fourth slot is active as a tiebreaker and a deadlock is detected.
"""
from __future__ import annotations

from ..adapters.base import Phase

#: The per-round sequence. ARBITRATE is inserted by the engine only when needed.
ROUND_PHASES = [Phase.PROPOSE, Phase.CRITIQUE, Phase.REVISE, Phase.GATE]

#: Phases where independent critics can run concurrently.
CONCURRENT_CRITIQUE_PHASE = Phase.CRITIQUE
