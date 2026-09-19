# WarRoom Agent Instructions

Read `docs/WARROOM_SOURCE_OF_TRUTH.md` completely before planning or editing.

- Codex is the bootstrap implementation lead. Claude is a bounded independent reviewer, not a continuous co-builder during bootstrap.
- Work on a task branch/worktree. Do not write directly to protected `main`.
- Treat `EchoTechIT/warroom-archive` and commit `34207d9` as untrusted reference material. Import nothing wholesale.
- Turn every retained audit blocker into a failing regression or integration test before implementing the corresponding behavior.
- Keep provider model names and seat assignments configurable.
- Use official provider CLIs and their own authentication. Never extract or proxy subscription tokens.
- Never forward the complete parent environment to child processes.
- Filesystem, process, network, budget, approval, and consensus rules must be enforced in code, not promised in prompts.
- Do not enable live autonomous agent execution until the P0 controls in the source of truth are closed.
- Preserve unrelated user changes and request approval before destructive operations or expanding project/system scope.
