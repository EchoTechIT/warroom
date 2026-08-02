"""Assemble each operator's per-turn prompt from its parts.

Because operators are stateless, the prompt is rebuilt from scratch every turn:

    [system: role charter]
    [task: the original spec]
    [context: marshaled transcript]
    [phase instruction: what to do THIS turn]
"""
from __future__ import annotations

from .adapters.base import Phase, Role

# Phase-specific instructions. Kept terse; the charter carries the role identity.
PHASE_INSTRUCTIONS = {
    (Role.ARCHITECT, Phase.PROPOSE): (
        "Produce the FIRST full draft of the artifact that satisfies the task. "
        "Be concrete and buildable. Output the artifact itself, not a plan to write it."
    ),
    (Role.ARCHITECT, Phase.REVISE): (
        "Revise the CURRENT ARTIFACT in light of the critiques above. For each "
        "objection, either integrate a fix or rebut it with a reason. Output the "
        "complete revised artifact."
    ),
    (Role.ARCHITECT, Phase.SYNTHESIZE): (
        "Emit the FINAL artifact plus a short change log of what the review "
        "changed. This is the deliverable."
    ),
    (Role.ADVERSARY, Phase.CRITIQUE): (
        "Attack the CURRENT ARTIFACT. Find the strongest specific, actionable "
        "objections — do not rubber-stamp. End your message with a fenced "
        "```verdict``` block: {\"certify\": <bool>, \"objections\": [<short strings>]}. "
        "Set certify=true ONLY if you have no material objection remaining."
    ),
    (Role.LOCAL, Phase.CRITIQUE): (
        "You are the fast local model. Do the cheap, high-value checks: does the "
        "artifact contradict anything earlier? Are there unstated assumptions, "
        "missing edge cases, or inconsistencies? Keep it tight and specific."
    ),
    (Role.FOURTH, Phase.ARBITRATE): (
        "The architect and adversary disagree. Weigh both sides and render a "
        "clear decision the architect must honor, with a one-paragraph rationale."
    ),
    (Role.FOURTH, Phase.CRITIQUE): (
        "Provide your specialist angle on the CURRENT ARTIFACT — the domain "
        "concern the others are least equipped to catch."
    ),
}


def instruction_for(role: Role, phase: Phase) -> str:
    return PHASE_INSTRUCTIONS.get(
        (role, phase),
        f"Act in your role ({role.value}) for the {phase.value} phase.",
    )


def assemble(*, charter: str, task: str, transcript: str, instruction: str, budget_hint: str = "") -> str:
    parts = [
        charter.strip(),
        "# TASK\n\n" + task.strip(),
    ]
    if transcript.strip():
        parts.append("# CONTEXT\n\n" + transcript.strip())
    parts.append("# YOUR TURN\n\n" + instruction.strip())
    if budget_hint:
        parts.append("# BUDGET\n\n" + budget_hint.strip())
    return "\n\n".join(parts).strip()
