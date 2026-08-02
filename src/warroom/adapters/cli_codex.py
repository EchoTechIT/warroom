"""Codex CLI adapter (ADVERSARY seat, ChatGPT Plus subscription).

Drives ``codex exec`` non-interactively. For a pure reviewer we run read-only
(``sandbox: read-only``) — we want text critique, not repo mutations.

STATUS: ``invoke`` is a **stub**; ``argv``/``parse``/``health_check`` are real.
Codex's machine-readable output is less stable than Claude Code's, so ``parse``
falls back to treating stdout as plain text — a deliberate, documented seam
(golden-file tested).
"""
from __future__ import annotations

import json
from typing import List

from .base import Status, TurnRequest, TurnResult, Usage
from .cli_base import CliShellAdapter


class CodexAdapter(CliShellAdapter):
    def argv(self, prompt: str) -> List[str]:
        args = list(self.cli.command) + list(self.cli.base_args)
        if self.cli.sandbox:
            args += ["--sandbox", self.cli.sandbox]
        if self.cli.prompt_via == "arg":
            args.append(prompt)
        return args

    def parse(self, stdout: str, stderr: str, returncode: int) -> TurnResult:
        if returncode != 0:
            if not stdout.strip():
                return self._unavailable(f"codex exited {returncode}: {stderr.strip()[:200]}")
            # Same rule as the Claude adapter: a non-zero exit with partial
            # output is a truncated stream, never an ok critique.
            return TurnResult(
                self.name, self.role, "", status=Status.ERROR,
                error=f"codex exited {returncode} with partial output: {stderr.strip()[:200]}",
                raw=stdout[:500],
            )

        # Prefer JSON if present (one object, or JSONL with a final message);
        # otherwise treat stdout as the plain critique text.
        text = stdout.strip()
        usage = Usage(metered=False)
        parsed_text = None
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "message" in evt or "text" in evt or "content" in evt:
                parsed_text = evt.get("message") or evt.get("text") or evt.get("content")
                u = evt.get("usage") or {}
                usage.input_tokens = int(u.get("input_tokens", 0))
                usage.output_tokens = int(u.get("output_tokens", 0))
                break
        content = (parsed_text or text).strip()
        if not content:
            return TurnResult(self.name, self.role, "", status=Status.EMPTY,
                              error="no output parsed", raw=stdout[:500])
        return TurnResult(self.name, self.role, content, status=Status.OK, usage=usage)

    async def invoke(self, turn: TurnRequest) -> TurnResult:
        # TODO(real): ``await self._spawn(getattr(turn, 'assembled_prompt'))``.
        canned = (
            "## Critique (stub: CodexAdapter)\n\n"
            "- Objection: the draft is a placeholder and asserts nothing testable.\n"
            "- Objection: no failure modes are enumerated.\n\n"
            "```verdict\n{\"certify\": false, \"objections\": [\"placeholder\", \"no failure modes\"]}\n```"
        )
        return TurnResult(self.name, self.role, canned, status=Status.OK,
                          usage=Usage(metered=False))
