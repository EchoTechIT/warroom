"""Shared subprocess plumbing for CLI-shell adapters (Claude Code, Codex).

Real behavior lives here; the per-tool subclasses only add argv construction and
output parsing. Design decisions the reviewer should note:

* Prompt is delivered on **stdin**, not argv — dodges shell escaping and
  arg-length limits. (``prompt_via: arg`` is supported but discouraged.)
* Commands run in a **scratch cwd** so relative-path writes land in a throwaway
  temp dir instead of the Warroom repo. This is hygiene, **not a sandbox**: a
  CLI that writes absolute paths can still reach the filesystem. Real isolation
  must come from the tool's own sandbox flags (``sandbox: read-only`` for a
  reviewer) or OS-level sandboxing around the whole Warroom process.
* We spawn with ``create_subprocess_exec`` (argv array, no shell) — never
  ``shell=True`` — in a **new session/process group**, and a timed-out or
  cancelled turn kills the whole group: an abandoned file-editing CLI must not
  keep running (and editing) after its turn is over.
* We rely on the CLI's *own* logged-in session for auth; Warroom stores no
  credentials.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import signal
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
                start_new_session=True,  # own process group -> the whole CLI tree is killable
            )
            try:
                out, err = await proc.communicate(input=stdin_bytes)
            except asyncio.CancelledError:
                # The policy layer's timeout cancels us here. Reap the child
                # before propagating — an orphaned CLI keeps running (and, for
                # a file-editing tool, keeps editing) long after its turn was
                # abandoned.
                self._kill(proc)
                await proc.wait()
                raise
            return self.parse(out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), proc.returncode or 0)
        finally:
            if tmp is not None:
                tmp.cleanup()

    @staticmethod
    def _kill(proc: "asyncio.subprocess.Process") -> None:
        """Kill the subprocess and its process group (CLIs spawn helpers)."""
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (AttributeError, ProcessLookupError, PermissionError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass

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
