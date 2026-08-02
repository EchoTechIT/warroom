"""Build an operator adapter from its validated config.

The registry is the one place adapter names map to classes. ``fake`` is included
so a panel can be assembled entirely from the in-repo fake adapter for offline
runs and tests.
"""
from __future__ import annotations

from ..config.models import OperatorConfig
from .base import OperatorAdapter
from .cli_claude_code import ClaudeCodeAdapter
from .cli_codex import CodexAdapter
from .http_openai import HttpOpenAIAdapter


def build_operator(name: str, cfg: OperatorConfig) -> OperatorAdapter:
    if cfg.adapter == "cli_claude_code":
        return ClaudeCodeAdapter(name, cfg.role, cfg.model, cfg.cli)  # type: ignore[arg-type]
    if cfg.adapter == "cli_codex":
        return CodexAdapter(name, cfg.role, cfg.model, cfg.cli)  # type: ignore[arg-type]
    if cfg.adapter == "http_openai":
        return HttpOpenAIAdapter(name, cfg.role, cfg.model, cfg.http)  # type: ignore[arg-type]
    if cfg.adapter == "fake":
        # Imported lazily so tests own the fake adapter without a production dep.
        from ..testing.fake_adapter import FakeAdapter
        return FakeAdapter(name, cfg.role, cfg.model)
    raise ValueError(f"unknown adapter: {cfg.adapter!r}")
