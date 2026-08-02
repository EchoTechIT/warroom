# 01 — Architecture

## The one contract

Every operator crosses a single seam, `OperatorAdapter`
([`src/warroom/adapters/base.py`](../src/warroom/adapters/base.py)):

```python
class OperatorAdapter(Protocol):
    name: str
    role: Role
    model_id: str
    async def health_check() -> HealthStatus
    async def invoke(turn: TurnRequest) -> TurnResult
```

`invoke` is **stateless**: `TurnRequest` carries role, system charter, the
original task, the marshaled transcript, the round number, the phase, and a
per-phase instruction. Nothing is remembered between calls because the operators
cannot see each other — the orchestrator supplies all context.

`TurnResult` normalizes every transport to `{content, status, usage, latency,
error}`. `Status` is the key enum:

| status | meaning | engine reaction |
|---|---|---|
| `OK` | usable content | append to transcript |
| `TIMEOUT` / `ERROR` | transient | retriable (bounded backoff) |
| `UNAVAILABLE` | rate-capped / not logged in / endpoint down | **skip, not fatal** |
| `EMPTY` | returned nothing / unparseable | soft failure, not retried |

`Usage.metered` is the cost fault line: subscription seats and Ollama are
unmetered (cost always 0); only cloud-API operators accrue dollars.

## Two adapter families

**CLI-shell** ([`cli_base.py`](../src/warroom/adapters/cli_base.py)) — real
subprocess plumbing shared by [`ClaudeCodeAdapter`](../src/warroom/adapters/cli_claude_code.py)
and [`CodexAdapter`](../src/warroom/adapters/cli_codex.py). Prompt on **stdin**
(no arg-length/escaping traps), spawned with `create_subprocess_exec` (argv
array, never a shell), in an **isolated scratch cwd** so a file-editing CLI can't
touch this repo. Auth is the CLI's own login; Warroom stores nothing.

**HTTP OpenAI-compatible** ([`http_openai.py`](../src/warroom/adapters/http_openai.py))
— one class for Ollama *and* any cloud endpoint; they differ only by `base_url`,
`api_key`, `model`, and price table.

Cross-cutting behavior (timeout, retry, availability) lives once in
[`invoke.py`](../src/warroom/invoke.py), not per adapter. Retry is bounded
exponential backoff with **injected** (default zero) jitter, so runs stay
reproducible and tests are stable.

## Orchestrator as memory

Operators share no memory, so the transcript
([`transcript.py`](../src/warroom/engine/transcript.py)) is the single source of
truth:

- Canonical storage is **JSONL**, one object per turn.
- Rendered to each operator as **attributed** markdown blocks
  (`### ROUND 2 · ADVERSARY (gpt-sol) · critique`). Attribution matters — the
  architect must know *who* said what to weigh authority.
- The **current artifact is always passed verbatim**, out of band from the
  discussion, so compaction can never summarize it away.
- **Compaction**: when a prompt would exceed `trigger_fraction × per_turn_token_cap`,
  older discussion (beyond the most recent round) is folded into a single
  *labeled* summary produced by the free local model. Summaries are marked as
  such so operators know fidelity is reduced.

## The round state machine

[`round_engine.py`](../src/warroom/engine/round_engine.py) walks an explicit
sequence — no hidden recursion, exactly so a reviewer can reason about it:

```
INTAKE
  └─ architect PROPOSE  → first draft becomes the artifact
ROUND n (1..max_rounds):
  CRITIQUE    adversary + local (+ fourth-as-specialist) run CONCURRENTLY
  REVISE      architect integrates/rebuts → new artifact; track "changed?"
  [ARBITRATE] fourth-as-tiebreaker, ONLY on a near-deadlock
  GATE        stop? (see termination)
SYNTHESIZE    architect emits final artifact + change log
EMIT          report.py writes the three artifacts
```

Independent critics in CRITIQUE run under `asyncio.gather`; the architect→critic
dependency is awaited in order.

## Termination — adversary-driven

[`termination.py`](../src/warroom/engine/termination.py). Three conditions,
first to fire wins:

1. **Consensus** — the adversary emits `{"certify": true}` in its fenced
   `verdict` block **and** the architect made no substantive change this round.
   A missing/malformed verdict is read as *not certified* — an unparseable
   review never counts as consensus.
2. **Fixed cap** — `max_rounds` reached (default 3).
3. **Budget / quorum** — a hard limit hit, or fewer than `quorum_min` operators
   available (need architect + ≥1 critic).

The default is deliberately **not** "architect satisfied" — that invites
sycophancy. The harder bar (the critic certifying) is the valuable one.

## Budget

[`budget.py`](../src/warroom/engine/budget.py). Asymmetric accounting: metered
(cloud) operators are gated by **dollars** (`max_cost_usd`); seats and Ollama by
**wall-clock and round count** (their real scarce resource is rate limits and
GPU time). Exhaustion is a clean terminal state → jump to SYNTHESIZE, flagged
`budget-truncated`.

## Graceful degradation

An operator that returns `UNAVAILABLE` (a rate-capped seat, a down endpoint) is
added to an unavailable set and skipped in subsequent turns. The run continues as
long as quorum holds; if it doesn't, GATE stops cleanly and SYNTHESIZE emits
whatever is current. This is a first-class branch, because subscription seats
*will* hit caps mid-run.
