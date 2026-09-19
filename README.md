# WarRoom

WarRoom is a self-hosted, LAN-first mission control for building personal software with multiple AI coding seats without manually shuttling prompts, files, and review notes between them.

## Current status

This is a clean project restart. The product direction, current seat assignments, security invariants, surviving audit findings, and build sequence live in [`docs/WARROOM_SOURCE_OF_TRUTH.md`](docs/WARROOM_SOURCE_OF_TRUTH.md).

No runnable application has been imported yet. The previous prototype contained useful engine ideas and tests, but also stubbed provider transports and unresolved safety defects. It remains available read-only in [`EchoTechIT/warroom-archive`](https://github.com/EchoTechIT/warroom-archive).

## Bootstrap team

- **Seat 1 — Codex:** primary architect and builder.
- **Seat 2 — Claude Code:** bounded independent reviewer after a coherent release-candidate handoff.
- **Seat 3 — Local Qwen model:** planned grunt-work seat on an AMD Radeon AI PRO R9700 32 GB.
- **Seat 4:** off for v1.

## First milestone

Build one complete Codex-only vertical slice:

> Create task in the UI → implement in an isolated git worktree → run tests → show progress and diff → request approval → merge.

Claude and the local seat are added only after that path is reliable and no longer requires the user to coordinate agents manually.

## Legacy provenance

- Original scaffold: [`641d87d`](https://github.com/EchoTechIT/warroom-archive/commit/641d87dbeb6171cdd8e2d011a87653fd1b668e42)
- Partially remediated prototype: [`34207d9`](https://github.com/EchoTechIT/warroom-archive/commit/34207d9751e95bb00df2c26fa2ac3f531e52bb89)

Legacy code is reference material, not a trusted base.

## License

MIT
