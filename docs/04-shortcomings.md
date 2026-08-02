# 04 — Shortcomings & Risks

Stated plainly. Each is a real weakness of *this* design; each has a mitigation
already reflected in the scaffold, and several remain open for Codex to probe.

## 1. Subscription-seat automation limits — the biggest risk

Claude Max and ChatGPT Plus are **subscription seats**, not API plans. Driving
them headless (`claude -p`, `codex exec`) is supported, but:

- They are **rate-limited** and can throttle, require re-auth, or hit daily caps
  mid-run.
- Automating them sits closer to the edge of each provider's terms than an API
  key does. Parallel fan-out especially so.

**Mitigation.** `UNAVAILABLE` is a non-fatal, first-class branch (skip + quorum
degrade). `warroom doctor` preflights each seat. Runs are human-paced (3 rounds
default), not a hammering loop. Warroom relies on the CLI's own login and stores
no credentials. **Open risk:** ToS acceptability of automation is the user's call;
Warroom does not and cannot guarantee it.

## 2. Model + CLI-format drift

`claude-fable-5` / `gpt-sol` aliases move, and the CLIs' JSON output schemas
change. A silent parser break would poison the transcript with garbage.

**Mitigation.** Aliases live in `operators.yaml`, not code. CLI parsing is behind
`parse()` methods with **golden-file tests** (`tests/adapters/test_cli_parsing.py`)
that fail loudly on a format change. Unparseable output → `EMPTY`, never passed
downstream. `warroom doctor` surfaces each live `model_id`.

## 3. No shared memory across operators

Coherence depends entirely on the marshaled transcript. Drop or mangle context
and the operators argue past each other.

**Mitigation.** Orchestrator-as-memory with canonical attributed JSONL; the
artifact is always passed verbatim; compaction only ever summarizes *older
discussion* and labels it as a summary. **Open risk:** long runs still compress
history; the summarizer is the free local model, whose fidelity is the weakest
link (see #4).

## 4. Local-model quality ceiling

A 32 GB open model is materially weaker than the cloud seats. If it were given
architect or sole-critic weight, output quality would drop — and it is also the
compaction summarizer.

**Mitigation.** The local role is scoped to summaries, consistency checks, and a
*secondary* critique voice — never the artifact owner, never the deciding vote.
Termination requires the **adversary** (a cloud seat) to certify, not the local
model. **Open risk:** compaction quality is bounded by the local model; a bad
summary can mislead later rounds.

## 5. GPU compatibility gap in the substrate

EchoTechAIStack's stock GPU overlay is **NVIDIA-only**; on the Arc B70 or R9700
Ollama silently runs on CPU.

**Mitigation.** Warroom is transport-decoupled (needs only the HTTP endpoint), so
the fix is in the substrate: the ROCm and Intel-Arc overlays in `deploy/`, plus a
planned `warroom doctor` GPU-liveness check (a trivial generation, not just a
ping). See [`03-hardware-substrate.md`](03-hardware-substrate.md).

## 6. Runaway cost on the metered fourth slot

A cloud tiebreaker invoked every round could surprise-bill.

**Mitigation.** `max_cost_usd` gates **metered** operators only; the fourth slot
defaults to `enabled: false` and, when on, `mode: tiebreaker` (invoked at most
once, at a deadlock) — not every round.

## 7. Scaffold-stage honesty

The three provider adapters' `invoke()` are **stubs** returning canned content.
The engine, config, transcript, termination, and reporting are real and tested,
but **no real model has been called yet**. This is intentional for the Codex
handoff (review the seams before the transports), and it is the first thing
`docs/05` tells the reviewer.

## Known open questions (handed to Codex)

- Is the consensus rule (`certify` **and** unchanged artifact) too eager or too
  strict? Could a stubborn architect + a lenient adversary certify a bad artifact?
- ~~The compaction summarizer runs a *synchronous* local call from inside an
  async engine and skips if a loop is already running — that path needs a
  proper async redesign.~~ **Resolved after the first adversarial review**: the
  review proved the shim was worse than flagged (inside the running engine it
  *always* failed, and the failure placeholder replaced real history).
  Compaction is now natively async (`round_engine._maybe_compact` awaits the
  local seat under a lock) and any summarizer failure leaves the transcript
  intact. See `docs/06-gpt-sol-review-response.md`.
- `architect_changed` is a normalized string inequality; a cosmetic reword counts
  as "changed" and blocks consensus. Is that the right sensitivity?
- No persistence/resume across process restarts; a killed run loses in-flight
  state beyond what's already on disk.
