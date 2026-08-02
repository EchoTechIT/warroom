"""Claude Code adapter (ARCHITECT seat, Claude Max subscription).

Drives ``claude -p`` headless with ``--output-format stream-json``. The seat's
own login provides auth — Warroom never sees a key.

STATUS: ``invoke`` is a **stub** that returns a canned draft so the engine runs
end-to-end offline. ``health_check`` and ``argv``/``parse`` are real; wiring the
real subprocess call is the ``# TODO(real)`` below, and the parse path is
exercised by ``tests/adapters/test_cli_parsing.py`` against captured fixtures.
"""
from __future__ import annotations

import json
from typing import List

from .base import Status, TurnRequest, TurnResult, Usage
from .cli_base import CliShellAdapter


class ClaudeCodeAdapter(CliShellAdapter):
    def argv(self, prompt: str) -> List[str]:
        args = list(self.cli.command) + list(self.cli.base_args) + ["--model", self.model_id]
        if self.cli.prompt_via == "arg":
            args.append(prompt)
        return args

    def parse(self, stdout: str, stderr: str, returncode: int) -> TurnResult:
        """Parse Claude Code ``stream-json`` output.

        Each line is a JSON event; the final assistant text is the concatenation
        of ``assistant`` message deltas, and usage arrives on a terminal
        ``result``/``message_stop`` event.
        """
        if returncode != 0 and not stdout.strip():
            # A non-zero exit with no output usually means a rate cap or a
            # not-logged-in seat -> treat as UNAVAILABLE, not a hard error.
            return self._unavailable(f"claude exited {returncode}: {stderr.strip()[:200]}")

        text_parts: List[str] = []
        usage = Usage(metered=False)  # flat-rate seat
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = evt.get("type")
            if etype == "assistant":
                msg = evt.get("message", {})
                for block in msg.get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
            elif etype in ("result", "message_stop"):
                u = evt.get("usage") or evt.get("message", {}).get("usage") or {}
                usage.input_tokens = int(u.get("input_tokens", usage.input_tokens))
                usage.output_tokens = int(u.get("output_tokens", usage.output_tokens))

        content = "".join(text_parts).strip()
        if not content:
            return TurnResult(self.name, self.role, "", status=Status.EMPTY,
                              error="no assistant text parsed", raw=stdout[:500])
        return TurnResult(self.name, self.role, content, status=Status.OK, usage=usage, raw=None)

    async def invoke(self, turn: TurnRequest) -> TurnResult:
        # TODO(real): call ``await self._spawn(getattr(turn, 'assembled_prompt'))``
        # once seat automation is validated. Canned response keeps the engine
        # runnable and deterministic for the Codex handoff.
        canned = (
            "## Draft (stub: ClaudeCodeAdapter)\n\n"
            f"Architect draft for task: {turn.task[:80]}\n\n"
            "This is a placeholder produced without calling the real CLI."
        )
        return TurnResult(self.name, self.role, canned, status=Status.OK,
                          usage=Usage(metered=False))
