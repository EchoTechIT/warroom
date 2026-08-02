"""Shared subprocess plumbing for CLI-shell adapters (Claude Code, Codex).

Real behavior lives here; the per-tool subclasses only add argv construction and
output parsing. Design decisions the reviewer should note:

* Prompt is delivered on **stdin**, not argv — dodges shell escaping and
  arg-length limits. (``prompt_via: arg`` is supported but discouraged.)
* Commands run in an **isolated scratch cwd** so a CLI that can edit files can
  never touch the Warroom repo.
* We spawn with ``create_subprocess_exec`` (argv array, no shell) — never
  ``shell=True``.
* We rely on the CLI's *own* logged-in session for auth; Warroom stores no
  credentials.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from typing import List, Optional

from ..config.models import CliConfig
from .base import (
    HealthStatus,
    OperatorAdapter,
    Role,
    Status,
    TurnRequest,
    TurnResult,
    Usage,
)


class CliShellAdapter(OperatorAdapter):
    """Base class. Subclasses set ``argv()`` and ``parse()``."""

    def __init__(self, name: str, role: Role, model: str, cli: CliConfig) -> None:
        self.name = name
        self.role = role
        self.model_id = model
        self.cli = cli
        self.total_timeout_s = cli.total_timeout_s

    # -- to be provided by subclasses -------------------------------------
    def argv(self, prompt: str) -> List[str]:
        raise NotImplementedError

    def parse(self, stdout: str, stderr: str, returncode: int) -> TurnResult:
        raise NotImplementedError

    # -- real plumbing -----------------------------------------------------
    async def health_check(self) -> HealthStatus:
        exe = self.cli.command[0]
        path = shutil.which(exe)
        if path is None:
            return HealthStatus(ok=False, detail=f"CLI not found on PATH: {exe!r}")
        return HealthStatus(ok=True, detail=f"found {exe} at {path}", model_id=self.model_id)

    async def _spawn(self, prompt: str) -> TurnResult:
        argv = self.argv(prompt)
        workdir: Optional[str] = None
        tmp = None
        if self.cli.workdir == "scratch":
            tmp = tempfile.TemporaryDirectory(prefix="warroom-")
            workdir = tmp.name

        stdin_bytes = prompt.encode("utf-8") if self.cli.prompt_via == "stdin" else None
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdin=asyncio.subprocess.PIPE if stdin_bytes is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                env=os.environ.copy(),
            )
            out, err = await proc.communicate(input=stdin_bytes)
            return self.parse(out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), proc.returncode or 0)
        finally:
            if tmp is not None:
                tmp.cleanup()

    async def invoke(self, turn: TurnRequest) -> TurnResult:  # pragma: no cover - overridden by stubs
        prompt = getattr(turn, "assembled_prompt", turn.phase_instruction)
        return await self._spawn(prompt)

    def _unavailable(self, detail: str) -> TurnResult:
        return TurnResult(
            operator_name=self.name,
            role=self.role,
            content="",
            status=Status.UNAVAILABLE,
            error=detail,
        )
