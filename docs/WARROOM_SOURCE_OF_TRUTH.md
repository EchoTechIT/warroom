# WarRoom — Source of Truth and Project Handoff

**Status:** pre-production scaffold; build not yet ready for live agents  
**Handoff date:** 2026-09-19  
**Active repository:** [EchoTechIT/warroom](https://github.com/EchoTechIT/warroom)  
**Archived prototype:** [EchoTechIT/warroom-archive](https://github.com/EchoTechIT/warroom-archive)  
**Repository reset completed:** 2026-09-19

This document replaces the scattered project exports as the authoritative statement of WarRoom's purpose, current state, seat assignments, safety rules, and next build plan. When older prompts, audits, reports, or repository docs disagree with this file, use this file for product intent and team roles. Code and tests remain authoritative for implemented behavior.

## 1. The product in one paragraph

WarRoom is a self-hosted, LAN-only mission control for building personal software with multiple AI coding seats without manual copy/paste. The user describes a task, Seat 1 plans and builds it in an isolated git worktree, automated checks run, another vendor can review the result, and the user sees a simple progress view, preview, diff, tests, and an approval button. The system should provide checks and balances against AI slop while hiding orchestration mechanics unless the user expands technical details.

## 2. Current decisions

### Team seats

| Seat | Assignment | Models and use | Access / hardware | Current status |
|---|---|---|---|---|
| **1 — Lead builder** | **Codex / OpenAI** | **Astra** for architecture, hard decisions, and final synthesis; **Sol** for substantial implementation and fallback architecture; **Terra/Luna** for bounded implementation subagents and mechanical work | Intended $100 Codex plan; official Codex surfaces only | **Selected as primary**. Codex owns the bootstrap build end to end. |
| **2 — Independent reviewer** | **Claude Code / Anthropic** | **Opus 5** for adversarial review and architecture review; **Sonnet 5** for review grunt work | Claude Pro $20, already purchased; official Claude Code CLI only | Available, but deliberately kept out of the construction loop until a coherent handoff exists |
| **3 — Local worker** | **Qwen-family local model** | Initial target: **Qwen3.8-27B at Q6**. Benchmark **Qwen3-Coder-30B-A3B at Q4_K_M** before locking the checkpoint; use whichever performs better on WarRoom's real grunt tasks | **AMD Radeon AI PRO R9700, 32 GB**, on Unraid/ROCm; expose an OpenAI-compatible LAN endpoint | Hardware/model direction selected; runtime and final checkpoint still need validation |
| **4 — Optional specialist** | Unassigned | Possible later research/theory/specialist seat | Subscription or second local endpoint | **Off for v1**; must not block the build |

Model names are configuration, not hard-coded architecture. If vendor catalogs change, the role stays stable and the configured model changes.

### Bootstrap operating mode

Until WarRoom can orchestrate itself:

1. Codex is the sole implementation lead and may use its own subagents.
2. Claude is invoked once at a coherent release-candidate handoff for independent review, with at most one bounded fix/recheck cycle.
3. The local seat and optional fourth seat do not block the initial build.
4. The user should not have to shuttle files, prompts, or review notes between products.

This is intentionally different from WarRoom's eventual steady-state multi-seat loop. The first job is to remove orchestration burden from the user.

## 3. Repository reality

### What exists

The attached legacy ZIP is an exact archive of commit [`641d87d`](https://github.com/EchoTechIT/warroom-archive/commit/641d87dbeb6171cdd8e2d011a87653fd1b668e42), formerly the prototype repository's default branch, `claude/warroom-program-analysis-bit4aa`.

That commit contains:

- a Python package and CLI;
- a deterministic `PROPOSE → CRITIQUE → REVISE → [ARBITRATE] → GATE → SYNTHESIZE` engine;
- configuration models, role charters, transcript/report code, and fake adapters;
- provider adapter parsers for Claude Code, Codex, and OpenAI-compatible HTTP;
- Docker overlay examples for AMD ROCm and Intel Arc;
- 26 tests reported as passing in the commit.

### What does not exist

- No frontend.
- No web backend/API or live event stream.
- No task board, feed, diff/review pane, approval flow, or project onboarding.
- No worktree-per-task controller.
- All three real provider `invoke()` methods are still stubs returning canned content.
- `doctor` does not prove that live subscription calls actually work.
- The scaffold is not safe to run as an autonomous coding system.

### The newer code branch

The archived repository contains a newer remediation commit, [`34207d9`](https://github.com/EchoTechIT/warroom-archive/commit/34207d9751e95bb00df2c26fa2ac3f531e52bb89), on branch `claude/gpt-sol-max-first-take-v06g9v`. It reports 44 passing tests and fixes several defects from the first adversarial review, including subprocess cleanup, partial-output handling, async compaction, stricter config parsing, current-artifact persistence, and fourth-seat mode wiring.

This is the best available starting code, but it is **not production-ready**. A later three-engine reconciliation reproduced additional open defects against `34207d9`.

Another branch, `claude/sols-audit-fable-opus-l0ezvg`, is one commit ahead of the default branch and only adds an audit document. Other research/hardware branches contain useful notes but are not a unified current implementation.

### Progress snapshot

| Area | State |
|---|---|
| Product purpose and user workflow | Defined |
| Seat strategy | Updated and defined in this document |
| Core round-engine prototype | Implemented, audited, and partially remediated |
| Real Codex / Claude / local invocation | Stubbed or unverified |
| Safety and consensus integrity | Known blockers remain |
| Backend service and persistence | Not built |
| Frontend | Not built |
| Worktree and approval enforcement | Not built |
| Unraid deployment | Prototype notes only |
| End-to-end live acceptance test | Not run |

## 4. Non-negotiable user experience

WarRoom is for a non-coder who wants working personal apps, not an orchestration console that requires babysitting.

The default UI must expose only:

1. **Create task:** plain-language goal, optional project/files, and a clear start button.
2. **Progress:** human-readable stage, active seat, elapsed time, and a stop button.
3. **Result:** preview, test status, concise explanation of what changed, and Approve / Request changes.
4. **History:** completed and failed runs with understandable reasons.

Technical transcripts, prompts, token details, raw logs, branches, and model routing should be available under expandable details, not placed in the primary path.

The first useful end-to-end flow is:

> Create task → Codex plans → Codex implements in a worktree → automated tests run → result and diff appear → user approves → merge.

Claude review becomes a one-click optional gate after that flow works. Seat 3 is added after its local endpoint is stable.

## 5. Required system behavior

### Project and task control

- One selected git repository is the project boundary.
- Each task gets its own branch and git worktree.
- Agents never write directly to `main`.
- Task state is durable across service restarts.
- Every task has explicit done criteria and a maximum number of review/fix rounds.
- The UI can cancel a run and the orchestrator must terminate the complete subprocess tree.

### Shared information without manual transfer

- The repository, task record, artifacts, test output, diffs, and structured handoffs are the shared memory.
- Agent turns are persisted as attributed events.
- Each seat receives only the relevant task context and file references, not an uncontrolled dump of all history.
- Structured handoff/verdict data must use a validated out-of-band schema; model-written Markdown must never control the state machine by regex alone.

### Human approval

The following require explicit user approval in the UI:

- merging to the protected branch;
- deleting user files or branches outside the current task worktree;
- installing packages or changing lockfiles when not already allowed by the task;
- expanding filesystem scope;
- adding a new external network destination;
- changing WarRoom's own role, permission, or safety configuration.

## 6. Security and reliability invariants

These are code-level requirements, not prompt instructions.

1. **Official access only.** Use official Codex and Claude Code CLIs authenticated through their own login flows. Do not extract, proxy, or reuse subscription OAuth tokens.
2. **Project-bounded filesystem.** A scratch working directory is hygiene, not isolation. Seat processes need enforceable filesystem boundaries and a single explicit writable worktree.
3. **Environment allowlist.** Never forward the complete parent environment. Each child receives only required variables and its own provider's auth/config paths.
4. **Network policy.** Default deny except the selected vendor CLI endpoints, configured local model endpoint, package registries when approved, and git remote operations when approved.
5. **Process ownership.** Every invocation has one process group, deadline, output bound, cancellation path, and guaranteed reap.
6. **Fail closed.** Parse errors, missing verdicts, empty outputs, lost architects, lost reviewers, stale artifacts, and budget exhaustion cannot be reported as successful consensus.
7. **Auditable decisions.** State transitions use validated structured records with actor, task, artifact digest, timestamps, and reason.
8. **Secrets stay segregated.** No transcript, report, prompt, browser payload, or child process receives unrelated credentials.

## 7. Consolidated open engineering blockers

The raw audits used different IDs and commits. The implementation should track the following consolidated controls instead of reopening duplicate findings.

### P0 — must close before live autonomous use

1. **Live adapters:** replace canned `invoke()` implementations with version-pinned, fixture-tested Codex, Claude Code, and OpenAI-compatible transports.
2. **Consensus proof:** consensus requires all of the following:
   - a live architect/owner at the gate;
   - a successful, non-empty revision in the current round;
   - an exact artifact digest being reviewed and certified;
   - exactly one schema-valid reviewer verdict delivered out of band;
   - `certify: true` only when `objections` is empty;
   - structural quorum requirements, not raw head count;
   - no post-certification rewrite unless it re-enters review.
3. **Execution isolation:** enforce worktree/filesystem boundaries, per-seat environment allowlists, network restrictions, and safe subprocess cancellation.
4. **Honest outcomes:** distinguish success, certified success, degraded output, cancellation, budget stop, and failure. CLI/API exit status must match the result.

### P1 — close before calling v1 reliable

5. **Atomic budgets:** reserve before calls, account for retries and compaction, reject non-finite/negative prices and limits, prevent spend from decreasing, and handle concurrent critics without unbounded overshoot.
6. **Prompt/transcript integrity:** fence operator content so it cannot forge role headers or current-artifact sections; avoid repeating full artifacts; preserve canonical history during compaction.
7. **Parser hardening:** accept only documented event types and string fields, reject partial non-zero exits, cap stdout/stderr, and keep golden fixtures for each supported CLI version.
8. **Configuration and doctor:** validate charter paths, required roles, positive limits, endpoint reachability, authentication, and a real headless smoke call. Missing or rate-limited seats must be reported honestly.
9. **Resume and recovery:** persist task state, current artifact digest, worktree, pending approval, and degraded conditions so restart does not manufacture a clean run.

### Lower-priority cleanup retained from the audits

- whitespace normalization can hide Markdown hard-break-only changes;
- tiebreaker arbitration can fire more than once near the round cap;
- transcript schema migration needs forward compatibility;
- rejected synthesis attempts should be explicitly labeled in persisted history;
- per-turn context caps must be enforced, not merely used as a compaction trigger.

## 8. Implementation direction

### Preserve these architectural ideas

- one self-hosted service for a single user;
- one mounted project boundary;
- worktree-per-task isolation;
- role/model mappings in configuration;
- a fake/demo panel for development without subscriptions;
- append-only events plus durable task state;
- official CLI adapters for subscription seats;
- OpenAI-compatible HTTP for the local seat;
- explicit approval gates and bounded review loops.

### First architecture checkpoint

Do not blindly implement the old Node-only build prompt or blindly extend the Python scaffold. The fastest default is to reuse the Python engine concepts and Pydantic models behind a small API, while building the UI in React/TypeScript. Codex should first compare:

- **reuse path:** harden `34207d9`, add a Python web service, persistence, worktrees, and the UI; versus
- **rewrite path:** retain tests/invariants and rebuild the orchestrator in TypeScript.

Choose the reuse path unless a short spike shows that the engine's safety defects make a rewrite cheaper. Record the decision in the repository before feature work.

Regardless of language, keep the runtime contract stable:

- task API;
- event stream via WebSocket or server-sent events;
- artifact/diff/test endpoints;
- approval actions;
- adapter interface;
- OpenAI-compatible local-model interface;
- Docker Compose deployment on Unraid.

### Recommended build sequence

1. **Repository reset — completed 2026-09-19.** The prototype is preserved read-only at `warroom-archive`; the active `warroom` repository has a clean history and current documentation only.
2. **Lock invariants with failing tests.** Convert the consolidated blockers into regression, integration, and abuse-case tests.
3. **Finish one live seat.** Make Codex Seat 1 execute a bounded task in a worktree with safe cancellation and durable logs.
4. **Build the thin backend.** Task state, event persistence, worktree lifecycle, tests, diffs, approvals, and restart recovery.
5. **Build the simple frontend.** Create task, progress, result/review, history, and doctor/settings.
6. **Complete the first vertical slice.** Codex-only task from UI through approved merge.
7. **Add Claude as a bounded final gate.** One independent review and one optional fix/recheck cycle, with no manual file transfer.
8. **Add Seat 3.** Validate ROCm/container access, compare the two local checkpoints, pin the winner, and use it only for bounded grunt work initially.
9. **Harden and package.** Fake-adapter demo, live smoke tests behind flags, backup/restore, Unraid template, and recovery documentation.

## 9. Definition of done for the first usable release

WarRoom v1 is usable when all of the following are demonstrated on the user's hardware:

- Docker Compose starts cleanly on Unraid.
- The browser UI can select a repository and create a task.
- Codex receives the task without copy/paste, works only in its task worktree, and streams understandable progress.
- A planted bug is caught by automated tests or the review gate.
- The UI shows the diff, test result, preview/artifact, and any degraded condition.
- Cancel kills the complete running process tree.
- Restart resumes or clearly marks an interrupted task; it never silently loses state.
- Approve merges the reviewed commit; reject leaves `main` unchanged.
- Claude can run a bounded final review from the same repository state without manual transfer.
- Secrets from one seat are not visible to another seat.
- The P0 and P1 controls above have automated regression coverage.

Seat 3 and Seat 4 are not required for the first Codex/Claude vertical slice, but Seat 3's HTTP adapter contract must already be stable.

## 10. Clean-repository migration status

Completed on 2026-09-19:

1. The prototype repository was renamed to `EchoTechIT/warroom-archive` and archived read-only; it was not deleted.
2. A fresh public `EchoTechIT/warroom` was created without the old branches or commit graph.
3. The new repository was seeded with this file, a concise README, license, ignore rules, and agent instructions.
4. Provenance links point back to the archived repository and the two important legacy commits (`641d87d` and `34207d9`).

Still required before implementation begins:

1. Configure branch protection/rulesets on the new `main` once the first implementation checks exist.
2. Use legacy commit `34207d9751e95bb00df2c26fa2ac3f531e52bb89` only as a reference during the reuse-vs-rewrite spike.
3. Copy only code and tests that survive review, in new focused commits. Do not treat the old tree as trusted simply because it had passing tests.

This gives the active project a clean history and current documentation without losing any prior research, audits, or prototype code. The archive remains available whenever a test, design idea, or implementation fragment is worth recovering.

## 11. Source disposition

Only this document needs to move into the dedicated WarRoom project as planning context. GitHub remains the code source.

| Existing source | Disposition | Information retained here |
|---|---|---|
| Attached `warroom-claude-warroom-program-analysis-bit4aa.zip` | Archive only | Exact `641d87d` baseline; GitHub supersedes the ZIP |
| `09-reconciled-findings.md` | Condensed; strongest audit source | Open/closed status against `34207d9` and consolidated controls |
| `17-ULTRACODE_BUILD_PROMPT-1-.md` | Superseded by this document | Mission-control UX, worktrees, shared context, approvals, Docker/Unraid goals |
| `18-final-audit-warroom.md` | Historical evidence; do not carry separately | Original critical/high/medium findings and safety invariants |
| `23-test_codex_adversarial_review.py` | Do not carry as a loose file | Its review tests were adopted and expanded on the `34207d9` branch |
| `16-05-codex-review-brief-1-.md` and `25-05-codex-review-brief.md` | Duplicate; already represented in GitHub history | Review target and attack surfaces |
| `22-ai-team-landscape-report-1-.md` and `24-ai-team-landscape-report-2-1-.md` | Exact duplicate; research archive only | Official-CLI constraint and shared-repo rationale |
| `WarRoom AI Coding Subscription Upgrade…md` | Historical decision input; recommendation superseded by actual usage preference | Model strengths, local-model candidates, and plan economics |
| `.url` shortcuts | Do not move | No unique project state |
| Small JSON exports and `users.json` | Do not move | Empty/unrelated project metadata |
| Unraid SMART ZIP | Do not move | Unrelated hardware diagnostic |
| Attention Dashboard ZIP | Do not move | Separate application |
| Usage screenshots | Do not move | Decision evidence already reflected in the Seat 1 choice |

## 12. Known decisions still to validate

These are implementation checkpoints, not reasons to delay the project split:

- confirm the exact Codex subscription tier when the live Seat 1 adapter is tested;
- choose the Seat 3 server/container after an R9700 ROCm smoke test;
- benchmark Qwen3.8-27B Q6 against Qwen3-Coder-30B-A3B Q4_K_M on WarRoom tasks;
- choose the backend implementation language after the reuse-vs-rewrite spike;
- confirm the repository path, protected branch, allowed package managers, and allowed outbound destinations;
- decide whether the LAN UI uses a shared password, reverse-proxy authentication, or both.

## 13. Short handoff to the next Codex session

> Treat this document as product authority. Work in the new clean `EchoTechIT/warroom`; consult the archived repository and commit `34207d9` only as legacy reference material. Do not import its branches or assume its code is safe. First reproduce the audit blockers as tests, choose and record reuse-vs-rewrite, then build one complete Codex-only vertical slice from UI task creation through safe worktree execution, tests, review display, approval, and merge. Keep Claude as one bounded final reviewer until the system can coordinate seats without user file shuttling. Do not enable the local or fourth seat as a dependency of the bootstrap release.
