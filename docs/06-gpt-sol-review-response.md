# 06 — Response to the First Adversarial Review (GPT Sol, max reasoning)

**Reviewer:** GPT Sol on max reasoning — the adversary seat itself, reviewing its
own war room. (The brief in [`05`](05-codex-review-brief.md) named Codex; the
seat that actually took the shot was Sol.)
**Deliverable received:** 14 failing tests, exactly as the brief requested.
**Ground truth at receipt:** 14/14 failed against the scaffold.
**Disposition:** 10 confirmed outright · 3 confirmed with corrected assertions ·
1 rebutted (with the underlying doc defect accepted). Zero misses on substance.

The adopted suite lives at [`tests/test_adversarial_gpt_sol.py`](../tests/test_adversarial_gpt_sol.py)
and is part of the permanent regression wall. This doc is the architect's reply:
what each finding was, what changed, and where the reviewer's asserts were wrong.

## Scorecard

| # | Finding (reviewer's test) | Verdict | Severity | Fix |
|---|---------------------------|---------|----------|-----|
| 1 | Quoted `verdict` block wins over the real one | **Confirmed** | High | last block wins (`termination.py`) |
| 2 | `"false"` string is truthy certification | **Confirmed** | High | `certify` must be JSON literal `true` |
| 3 | `_norm` erases indentation → semantic change reads "stable" | **Confirmed** | High | line-structure-preserving `_norm` |
| 4 | Compaction replaces history with a nested-loop placeholder | **Confirmed** | High (data loss) | natively async compaction; failure leaves history intact |
| 5 | Timeout orphans the CLI subprocess | **Confirmed** | High | own process group + kill on cancellation (`cli_base.py`) |
| 6 | Non-zero exit with partial stdout parsed as OK | **Confirmed** | Medium-High | non-zero is never OK: ERROR (retriable) with output, UNAVAILABLE without (both CLI adapters) |
| 7 | Certified artifact replaced wholesale at SYNTHESIZE | **Confirmed, assert kept** | High (design) | consensus guard: synthesis must carry the certified artifact or it doesn't replace it |
| 8 | EMPTY critic counts toward quorum forever | **Confirmed** | Medium | GATE quorum counts critics by delivery this round |
| 9 | `max_rouds` typo silently ignored; zero-price metered table passes | **Confirmed** | Medium | `extra="forbid"` on all config models; metered requires a non-zero price |
| 10 | JSONL round-trip drops `current_artifact` | **Confirmed** | Medium | artifact record persisted in the JSONL |
| 11 | Budget cap crossed → engine still spends a full round | **Confirmed, assert corrected** | Medium-High | pre-call `hard_stop` gate; overshoot bounded to the one in-flight call |
| 12 | Fourth-as-specialist never critiques | **Confirmed, assert corrected** | Medium | `fourth_mode` wired config → CLI → engine; specialist critiques every round, tiebreaker arbitrates only |
| 13 | Unavailable architect returns a normal-looking empty result | **Confirmed, assert corrected** | Medium | explicit `RunResult.failed` + run-report banner |
| 14 | Scratch cwd is not filesystem isolation | **Rebutted** (test) / **accepted** (docs) | Doc | overclaims removed; honest hygiene test adopted |

## The three corrected assertions

The reviewer's failure scenarios were real in all three; the demanded behavior
was not physically achievable, so the adopted tests pin the honest invariant
instead.

**Budget (#11).** The original asserted `spent_usd <= cap`. A call's cost is
unknowable until it returns, so the cap can always be crossed by exactly one
in-flight call — no engine can do better without pre-metering, which
subscription CLIs don't offer. What *was* broken: the budget was only consulted
at GATE, so a crossed cap still bought the rest of the round — critique, revise,
arbitrate, synthesize — an 8× overshoot in the reviewer's own scenario. The
engine now checks `Budget.hard_stop()` before **every** call. Adopted invariant:
spend stops at first crossing (`spent == 1.0` on a `$0.50` cap, architect called
once, adversary never).

**Unavailable architect (#13).** The original asserted a non-empty final
artifact. With the architect down from PROPOSE onward there is nothing to
return, and inventing content would be worse than none. What *was* broken: the
run ended looking normal — `truncated=False`, no failure marker, an empty
`final_artifact.md` written as if reviewed. Adopted invariant:
`RunResult.failed is True`, quorum-lost stop reason, and a **RUN FAILED** banner
in the report.

**Fourth-as-specialist (#12).** The original expected the fourth seat in
CRITIQUE by default. Participation is a config decision — `fourth.mode:
tiebreaker | specialist | off` — and tiebreaker is the documented default
(shortcomings §6: the metered fourth is invoked *at most once, at a deadlock*,
precisely to bound cost). What *was* broken: `mode` was parsed, validated, and
then never threaded into the engine at all — the engine docstring even claimed
specialist critique participation. `fourth_mode` now flows config → CLI →
engine; the adopted tests pin both modes.

## The rebuttal

**Scratch cwd (#14).** The test wrote to an absolute path from inside the
subprocess and asserted the file stayed untouched. No working directory can
stop an absolute-path write; satisfying that assert requires OS-level
sandboxing (or the CLI's own sandbox flag), which the scaffold deliberately
does not claim to implement. What the reviewer *did* catch is that the docs
claimed it anyway — "isolated scratch cwd so a file-editing CLI can never touch
the Warroom repo" was an overclaim. That language is gone from `cli_base.py`,
`docs/01`, and `operators.yaml`: scratch cwd is **relative-path hygiene, not a
sandbox**; real isolation is the tool's own `sandbox: read-only` or OS
sandboxing around the Warroom process. The adopted test pins the hygiene that
is actually provided.

## Design notes recorded while fixing

- **Certification is now strict in three stacked ways** (#1, #2, #7): the
  terminal verdict block speaks, only the JSON literal `true` certifies, and a
  certified artifact survives synthesis unless the synthesis carries it
  verbatim (modulo whitespace normalization — a change log *appended* to the
  certified text is the intended shape and passes the guard).
- **`_norm` now errs toward false-positive change** (#3): intra-line spacing
  differences count as change. Per the open question in
  [`04`](04-shortcomings.md), over-sensitivity can only delay consensus; the
  bug it replaces could *manufacture* consensus on a semantically different
  artifact. That trade is taken deliberately.
- **Compaction can now only shrink history into a real summary** (#4): no
  summarizer, a failed call, a timeout, or an empty result all leave the
  transcript verbatim. The failure placeholder path is gone, not patched —
  there is no code path that folds turns into anything but local-model output.
- **EMPTY stays a soft failure for the *seat*, but not for the *round*** (#8):
  the seat isn't marked unavailable (a later round may recover), yet a round in
  which no critic delivered cannot hold quorum, so a permanently silent panel
  now terminates as `quorum lost` instead of masquerading as a completed
  review.

## Status after this round

All 14 findings are closed: fixed, or rebutted with the underlying doc defect
fixed. Full suite: 44 tests green (26 pre-existing + 18 adopted/companion).
The `05` brief's known-weak-spots list is updated in
[`04`](04-shortcomings.md) — the async-compaction open question is resolved;
the consensus-eagerness and resume questions remain open for the next take.
