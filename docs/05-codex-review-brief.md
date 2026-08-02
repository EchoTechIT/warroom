# 05 — Codex Adversarial-Review Brief

**Reviewer:** OpenAI Codex, acting as the adversarial colleague.
**Posture:** try to break this. Your job is to find the strongest, most specific
objections — not to approve. Approval without a sharp objection is worthless here.

## What you're reviewing

A **docs + scaffold** stage of Warroom, a multi-operator AI war room. The engine,
config, transcript, termination, and CLI are real and run end-to-end against a
process-free fake panel. The three provider adapters are **stubs** (real
`health_check()` + real parsing, canned `invoke()`), marked `# TODO(real)`. Do
**not** file "the adapters don't call real models" as a finding — that's the
declared scope. Attack the *design and the seams*.

## Run it yourself first (5 minutes, no external processes)

```bash
pip install -e ".[dev]"
pytest -q                                   # config, transcript, termination, CLI-parsing
warroom --panel fake doctor                 # validates config + health-checks the panel
warroom --panel fake run "Design a rate limiter for a homelab API gateway"
cat runs/*/run_report.md runs/*/final_artifact.md
```

The fake panel is scripted to converge via the **consensus** gate at round 2
(adversary certifies + artifact stable) — so a green run exercises the
adversary-driven termination path, not just the round cap.

## The seams to attack, in priority order

1. **Transport boundary** (`src/warroom/adapters/base.py`, `cli_base.py`,
   `http_openai.py`). Is `OperatorAdapter` genuinely sufficient for *both* a
   subprocess CLI and a streaming HTTP endpoint? What breaks when a CLI writes to
   stderr, exits non-zero with partial stdout, or blocks on stdin? Is the
   stdin/scratch-cwd isolation actually safe for a file-editing CLI?

2. **Transcript marshaling & compaction** (`engine/transcript.py`). Can the
   attributed rendering be spoofed by operator content that itself contains
   `### ROUND ...` headers? Does compaction ever drop or reorder turns
   incorrectly? The artifact is supposed to be *unsummarizable* — prove or
   disprove that it can't leak into the compacted discussion.

3. **Termination correctness** (`engine/termination.py`, `round_engine.py`).
   - The verdict regex parses a fenced ```verdict``` block. Can an architect's
     text, quoted critique, or a code sample inject a false `{"certify": true}`?
   - Consensus = `certify` **and** `architect_changed == False`. Construct a case
     where a bad artifact gets certified (lenient adversary) or a good one never
     converges (cosmetic rewords keep `architect_changed` true).
   - Does the loop ever fail to terminate, or terminate with no artifact?

4. **Seat-limit / availability handling** (`invoke.py`, `round_engine.py`). Trace
   what happens when the architect goes `UNAVAILABLE` mid-run vs. a critic.
   Does quorum logic actually hold? Is retry ever applied to a non-retriable
   status? Can a `TIMEOUT` on the architect strand the run?

5. **Config validation & fourth-slot resolution** (`config/models.py`,
   `config/loader.py`). Is `resolve_fourth` correct for every
   `enabled`/`mode`/`variant` combination? Does `--panel fake`'s
   `model_copy(update=...)` bypass a validator that should have fired? Can a
   metered operator slip through without a price table?

6. **Budget accounting** (`engine/budget.py`). Metered-vs-unmetered gating: can a
   local/seat operator ever accrue dollars, or a cloud operator escape the
   dollar gate? Is wall-clock measured from a stable monotonic base?

## Known-weak spots we already flagged (confirm or deepen)

See [`04-shortcomings.md`](04-shortcomings.md) §"Known open questions":
the synchronous compaction summarizer inside the async engine, the
`architect_changed` sensitivity, the consensus eagerness, and the lack of
resume. We expect you to either escalate these or find we've understated them.

## Deliverable back to us

For each finding: the file/line, a **concrete failure scenario** (inputs → wrong
behavior), and severity. Rank most-severe first. Where you can, express it as a
failing test we can drop into `tests/`.
