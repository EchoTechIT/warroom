# WarRoom Preservation Manifest

**Audit completed:** 2026-09-19  
**Purpose:** prove what was inspected, retained, and deliberately excluded while separating WarRoom from the broader homelab project.

## 1. Result

No required WarRoom material is being left solely in the mixed homelab project.

The carry-forward set is:

1. `docs/WARROOM_SOURCE_OF_TRUTH.md` — product, architecture, security, seat topology, blockers, and build order.
2. `docs/PRODUCT_UI_SPEC.md` — recovered and reconciled UI/UX requirements.
3. `docs/decisions/0001-seat-topology.md` — why Codex leads bootstrap and Claude reviews.
4. `docs/PRESERVATION_MANIFEST.md` — this audit trail.
5. `AGENTS.md`, `CLAUDE.md`, `README.md`, `.gitignore`, and `LICENSE`.
6. The read-only [`EchoTechIT/warroom-archive`](https://github.com/EchoTechIT/warroom-archive), including every legacy branch and commit.
7. A downloadable handoff ZIP containing the canonical set plus the small number of unique raw WarRoom evidence files that are not necessary in the active repository.

## 2. Important negative finding: no surviving visual UI artifact

The inventory found no WarRoom Figma file, screenshot, HTML mockup, React frontend, or runnable UI prototype. The archived GitHub tree contains backend/orchestration Python only. The old UI concepts existed as prose in `ULTRACODE_BUILD_PROMPT(1).md`; they are now captured in `PRODUCT_UI_SPEC.md`.

The five `.url` shortcuts were opened and identified as:

- EchoTechHomelab Network Emblem;
- EchoTechIT Futuristic Tech Emblem;
- EchoTechPCs marketplace badge;
- EchoTechIT Cybersecurity Emblem;
- EchoTechPCs circular logo.

They are brand assets for other EchoTech projects, not WarRoom designs.

## 3. Supplied-file disposition

| Source | Classification | Disposition |
| --- | --- | --- |
| `warroom-claude-warroom-program-analysis-bit4aa.zip` | WarRoom legacy code | Exact baseline `641d87d`; superseded by the archived GitHub repository, which retains later fixes and every branch |
| `reconciled-findings.md` | WarRoom, unique audit reconciliation | Retained in the downloadable legacy-evidence bundle; active controls are consolidated in the source of truth |
| `ULTRACODE_BUILD_PROMPT(1).md` | WarRoom, outdated build prompt with unique UI prose | Retained in the downloadable legacy-evidence bundle; UI requirements promoted into `PRODUCT_UI_SPEC.md` |
| `final-audit-warroom.md` | WarRoom audit evidence | Retained in the downloadable legacy-evidence bundle; equivalent audit branch remains in GitHub |
| `test_codex_adversarial_review.py` | WarRoom review probes | Retained as evidence only; corrected/adopted suite is at archive commit `34207d9` and must not be dropped into the new test tree unchanged |
| `05-codex-review-brief(1).md` and `05-codex-review-brief.md` | Exact duplicates | No duplicate carried; canonical version remains in archived Git history |
| `ai-team-landscape-report(1).md` and `ai-team-landscape-report 2(1).md` | Exact duplicates | One copy retained in the downloadable legacy-evidence bundle; current decisions moved into source of truth and ADR 0001 |
| Subscription-upgrade report | WarRoom decision evidence | Retained in the downloadable legacy-evidence bundle; recommendation was superseded by observed usage and ADR 0001 |
| Two reconstructed seat-strategy briefs | WarRoom decision evidence | Condensed into ADR 0001; raw files remain in the downloadable legacy-evidence bundle |
| `IMG_6941.png`, `IMG_6942.png` | Usage screenshots | Not placed in the public repo; conclusions are retained without exposing account-usage screenshots |
| Five ChatGPT `.url` files | Other EchoTech brand projects | Excluded from WarRoom after live identification; no WarRoom state inside |
| Three project metadata JSON files | EchoTechPCs, PC Optimization, EchoTechLLC | Excluded as unrelated |
| Six conversation JSON files | Empty stubs for Design System, Nocturne, Untitled, or Classical projects | Excluded; zero messages and no recoverable design content |
| `users.json` | Empty/minimal export metadata | Excluded; no WarRoom content |
| `attention-dashboard.zip` | Separate self-hosted application | Excluded from WarRoom; keep with its own project |
| `echotechunraid-smart-20260729-1817(1).zip` | Unraid/NVMe diagnostic | Excluded; includes a drive serial number and must not enter the public WarRoom repo |

## 4. Duplicate verification

- The two `05-codex-review-brief` files have the same SHA-256: `3f88bdc430f92e9849cb4522c9b0b2058245c6c2a920071dd18031a203b90c4b`.
- The two AI landscape reports have the same SHA-256: `bb6d564b6b4c6eebf0ab2f22ba1a91cfb55cce848649f72563218e40588340aa`.
- The standalone legacy ZIP identifies baseline commit `641d87dbeb6171cdd8e2d011a87653fd1b668e42`.

## 5. Archived GitHub coverage

Every branch in `EchoTechIT/warroom-archive` was enumerated and its complete recursive tree inspected:

| Branch | Tip | Unique value |
| --- | --- | --- |
| `claude/warroom-program-analysis-bit4aa` | `641d87d` | Initial 26-test scaffold |
| `claude/sols-audit-fable-opus-l0ezvg` | `6461e94` | Independent Fable/Opus audit |
| `claude/gpt-sol-max-first-take-v06g9v` | `34207d9` | Corrected fixes and 44-test regression wall |
| `echotechitdeploy` | `248ff27` | Merged deployment branch with the same final tree as `34207d9` |
| `claude/homelab-ai-strategy-hoe9wz` | `ad677eb` | R9700/OptiPlex integration and old seat-map notes |
| `claude/gpu-upgrade-decision-c79m1e` | `8f9752d` | Historical GPU decision notes |

No branch contains frontend files. The legacy engine remains available for the reuse-versus-rewrite spike, but it is not trusted production code.

## 6. Canonical authority order

When sources disagree, use this order:

1. current implementation and passing security/acceptance tests;
2. `docs/WARROOM_SOURCE_OF_TRUTH.md`;
3. `docs/PRODUCT_UI_SPEC.md` for interface behavior;
4. accepted decision records in `docs/decisions/`;
5. this manifest for provenance;
6. archived commits and raw evidence for historical investigation only.

Old model names, subscription assignments, hardware assumptions, and architecture choices in legacy documents are not active requirements.

## 7. Material intentionally kept out of the active repository

The downloadable handoff carries raw WarRoom evidence so it cannot be lost during project cleanup. The public active repository does not carry:

- duplicate reports;
- screenshots of subscription usage;
- hardware diagnostics or serial numbers;
- unrelated application code;
- empty export metadata;
- the full untrusted legacy source tree.

This keeps the new repository understandable without making the archive or evidence disappear.
