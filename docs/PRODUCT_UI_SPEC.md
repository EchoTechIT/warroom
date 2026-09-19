# WarRoom Product and UI Specification

**Status:** authoritative for the bootstrap UI  
**Updated:** 2026-09-19  
**Product authority:** [`WARROOM_SOURCE_OF_TRUTH.md`](WARROOM_SOURCE_OF_TRUTH.md)

## 1. Purpose

WarRoom is a self-hosted, LAN-first mission control for a non-coder who wants AI agents to build useful personal software without manually moving prompts, patches, or review notes between vendors.

The interface must make the safe path obvious:

> Describe the task → watch understandable progress → inspect the result → approve or reject the merge.

The interface is not primarily an agent chat room, a token dashboard, or an IDE. Those details remain available, but they are secondary to the task and approval flow.

## 2. Preservation finding

An exhaustive pass of the supplied project files, ZIP archives, five shared ChatGPT links, and all six branches of `EchoTechIT/warroom-archive` found **no surviving WarRoom visual mockup, screenshot, Figma file, HTML prototype, React component, or runnable frontend**.

The five shared links are EchoTech brand/logo images, not WarRoom UI. The archived repository is a Python orchestration scaffold with documentation and tests only. Therefore, this document is the recovered design source of truth. It combines the useful UI requirements from the old `ULTRACODE_BUILD_PROMPT` with the simplified bootstrap flow selected in the current source of truth.

## 3. Product principles

1. **Outcome first.** The primary view says what is happening, whether it worked, and what the user must decide.
2. **Progressive disclosure.** Raw prompts, transcripts, branches, tool calls, token details, and logs live behind expandable technical details.
3. **No fake certainty.** Success, certified success, degraded output, cancellation, budget stop, and failure are visually and textually distinct.
4. **Approval is explicit.** Merging, scope expansion, package installation, destructive changes, and new network destinations never look like routine progress.
5. **Every action has provenance.** The UI can identify the seat, task, artifact digest, tests, and reason behind every state transition.
6. **Offline seats do not break navigation.** Missing, throttled, or unauthenticated seats show a clear degraded state and recovery action.
7. **Usable from a phone.** The full review may be easier on desktop, but task creation, status checks, cancellation, and approval decisions must work on mobile.

## 4. Navigation

The bootstrap release has five top-level destinations:

| Destination | Primary purpose |
| --- | --- |
| **Tasks** | Create a task and see active work |
| **Run detail** | Follow one task from plan through result |
| **Review** | Inspect tests, preview, changes, and approval requests |
| **History** | Find completed, rejected, cancelled, degraded, and failed runs |
| **Doctor & settings** | Check seats, repositories, limits, and security posture |

On desktop, use a compact left rail. On mobile, use a bottom navigation bar for Tasks, History, and Doctor; Run detail and Review are contextual pages.

## 5. Core screens

### 5.1 Tasks / home

The top of the page contains a plain-language task composer:

- goal or request;
- selected repository;
- optional files or folders;
- optional done criteria;
- a clear **Start task** button.

Below it, show active tasks as cards or a compact board grouped by human-readable state:

- Waiting;
- Planning;
- Building;
- Testing;
- Reviewing;
- Needs approval;
- Complete;
- Blocked or failed.

Each task summary shows title, current stage, active seat, elapsed time, last meaningful event, and whether user action is required. Avoid exposing internal state names as the only label.

### 5.2 Run detail

The default view contains:

- task goal and repository;
- current human-readable stage;
- active seat and model family;
- elapsed time and bounded-budget status;
- a chronological progress feed written for a non-coder;
- **Stop** button with confirmation;
- clear degraded or blocked banner when applicable.

Expandable **Technical details** contain the attributed event stream, exact commands, worktree/branch, prompts, raw logs, retries, model routing, and artifact digests.

The older “war-room feed” concept survives here as an advanced view: attributed seat messages can be rendered like a threaded group conversation, but it must not replace the concise progress summary.

### 5.3 Review

The review page answers four questions in this order:

1. What was produced?
2. Did the checks pass?
3. What changed?
4. What decision is being requested?

Required sections:

- preview or downloadable artifact;
- concise change summary;
- automated test result with failures expanded by default;
- independent-review result when Claude is enabled;
- changed-file list and unified diff;
- security or scope warnings;
- pending approval request and reason.

Primary actions:

- **Approve and merge**;
- **Request changes**;
- **Reject**;
- **Kill run** when still active.

Approval must display the exact repository, source branch/worktree, target branch, commit or artifact digest, test status, and any degraded conditions. A disabled approval control must explain why.

### 5.4 History

History supports search and filtering by repository, outcome, seat, and date. Each record shows:

- request summary;
- outcome badge;
- completed stage or failure point;
- duration;
- tests and review status;
- merge commit when applicable;
- concise reason for failure, rejection, cancellation, or degradation.

Opening an item reconstructs its persisted run detail and review evidence. Restart recovery must not create a clean-looking replacement record.

### 5.5 Doctor & settings

Doctor distinguishes:

- CLI missing;
- installed but unauthenticated;
- authenticated but headless smoke call failed;
- rate-limited or usage-exhausted;
- healthy;
- local endpoint reachable but not GPU-accelerated;
- local endpoint unavailable.

For each seat, show configured role, provider, selected model, last successful smoke test, and local call/turn counters. Vendor quota links may be provided, but WarRoom must not pretend it can read quotas that vendors do not expose.

Settings cover:

- repository allowlist and protected branch;
- role-to-seat mapping;
- per-task rounds and call budgets;
- permitted package managers and network destinations;
- local-model endpoint;
- authentication mode for the LAN UI;
- backup and restore status.

Dangerous settings changes require the same explicit approval treatment as a merge.

## 6. State and outcome language

| Internal condition | User-facing label | Required treatment |
| --- | --- | --- |
| Queued or awaiting a seat | Waiting | Neutral; explain dependency |
| Agent actively working | Planning / Building / Reviewing | Animated but not distracting |
| Automated checks running | Testing | Show current suite and elapsed time |
| User decision required | Needs approval | High-visibility callout |
| All required checks passed and merge completed | Complete | Positive confirmation with commit |
| Useful artifact exists but a seat/check was unavailable | Degraded | Amber warning; never call certified |
| User cancelled | Cancelled | Neutral final state with cleanup result |
| Budget or usage limit stopped work | Limit reached | Explain which limit and preserved state |
| Safety boundary or prerequisite prevented work | Blocked | Explain required corrective action |
| Execution failed | Failed | Red status with failure stage and evidence |

Color is supplemental. Every state must also use text and an icon.

## 7. Approval interactions

The following always interrupt the normal flow with a dedicated request:

- merge to the protected branch;
- deletion outside the task worktree;
- package installation or unexpected lockfile change;
- filesystem scope expansion;
- new outbound network destination;
- role, permission, or safety-configuration change.

Each request shows **what**, **why**, **scope**, **initiating seat**, and **consequence**. Approval is single-use and bound to the displayed action and artifact digest. An agent cannot manufacture an approval by writing text that resembles a UI request.

## 8. Visual direction

- Dark by default, dense but calm, with strong information hierarchy.
- Utilitarian mission-control character without military cosplay or excessive neon.
- Clear typography and compact spacing for logs/diffs; more breathing room around decisions.
- Seat identity may use stable colors and avatars, but provider branding must not dominate the product.
- Keyboard-friendly on desktop with a visible shortcut reference.
- Responsive layouts must avoid horizontal scrolling except inside diffs and code blocks.
- Respect reduced-motion preferences and WCAG AA contrast.

No undocumented visual mockup should be treated as authoritative. New mockups should be evaluated against this behavior specification.

## 9. Bootstrap scope

The first vertical slice implements only:

1. select a repository;
2. create a task;
3. show Codex planning/build progress;
4. run automated tests;
5. show result, preview/artifact, diff, and failures;
6. cancel safely;
7. approve or reject the merge;
8. persist the record across restart.

Claude review is one optional final gate after this works. The local seat and fourth seat must not block the bootstrap UI.

## 10. UI acceptance tests

- A first-time non-coder can create a bounded task without understanding branches, worktrees, prompts, or model routing.
- Every active task displays one truthful current stage and one obvious stop control.
- A failed or degraded run cannot be mistaken for a successful certified run.
- Approval cannot be submitted without seeing target branch, change summary, tests, and artifact identity.
- Cancelling a run updates the UI only after the complete process tree is terminated or cleanup failure is reported.
- Refreshing or restarting reconstructs the same task state and pending approval.
- Keyboard-only and mobile users can create, inspect, cancel, request changes, and approve.
- Demo mode can exercise the full UI without paid subscriptions.

## 11. Provenance

This specification retains the useful UI ideas from the July 2026 legacy build prompt—task board, attributed feed, review pane, doctor page, dark/keyboard-friendly presentation, WebSocket-style live progress—and reconciles them with the September 2026 decision to simplify the default experience around Create, Progress, Result, and History.

The raw legacy prompt and its associated research remain preserved in the project handoff package. They are historical evidence, not current product authority.
