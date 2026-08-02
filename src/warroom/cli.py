"""Warroom command line: ``warroom run "<task>"`` and ``warroom doctor``.

Implemented on the standard library's ``argparse`` (not Typer) so the runnable
skeleton has no hard CLI dependency — the offline path needs only ``pydantic``
and ``pyyaml``. Swapping in Typer/rich later is a drop-in enhancement.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import sys
from pathlib import Path
from typing import Dict

from .adapters.base import OperatorAdapter, Role
from .adapters.registry import build_operator
from .config.loader import load_operators, load_run_policy, resolve_fourth
from .config.models import OperatorConfig
from .engine.budget import Budget
from .engine.round_engine import RoundEngine
from .report import emit, run_dir


def _load_charters(panel_cfg: Dict[str, OperatorConfig], base: Path) -> Dict[Role, str]:
    charters: Dict[Role, str] = {}
    for cfg in panel_cfg.values():
        if cfg.charter:
            p = (base / cfg.charter)
            if p.exists():
                charters[cfg.role] = p.read_text(encoding="utf-8")
    return charters


def _build_panel(panel_cfg: Dict[str, OperatorConfig], force_fake: bool) -> Dict[str, OperatorAdapter]:
    panel: Dict[str, OperatorAdapter] = {}
    for name, cfg in panel_cfg.items():
        if force_fake:
            cfg = cfg.model_copy(update={"adapter": "fake"})
        panel[name] = build_operator(name, cfg)
    return panel


def cmd_doctor(args: argparse.Namespace) -> int:
    base = Path(args.operators).parent
    spec = load_operators(args.operators)
    policy = load_run_policy(args.policy)
    panel_cfg, note = resolve_fourth(spec)
    panel = _build_panel(panel_cfg, force_fake=args.panel == "fake")

    print(f"warroom doctor — {note}")
    print(f"run policy: max_rounds={policy.run.max_rounds}, "
          f"max_cost_usd=${policy.run.max_cost_usd}, quorum>={policy.run.quorum_min_operators}")
    print("panel:")

    async def _check() -> int:
        rc = 0
        for name, adapter in panel.items():
            h = await adapter.health_check()
            flag = "OK " if h.ok else "XX "
            if not h.ok:
                rc = 1
            print(f"  [{flag}] {name:12s} role={adapter.role.value:9s} "
                  f"model={adapter.model_id:20s} {h.detail}")
        return rc

    return asyncio.run(_check())


def cmd_run(args: argparse.Namespace) -> int:
    base = Path(args.operators).parent
    spec = load_operators(args.operators)
    policy = load_run_policy(args.policy)
    panel_cfg, note = resolve_fourth(spec)
    panel = _build_panel(panel_cfg, force_fake=args.panel == "fake")
    charters = _load_charters(panel_cfg, base)

    budget = Budget(
        max_rounds=policy.run.max_rounds,
        max_wall_clock_s=policy.run.max_wall_clock_s,
        max_cost_usd=policy.run.max_cost_usd,
        per_turn_token_cap=policy.run.per_turn_token_cap,
    )
    engine = RoundEngine(
        panel=panel,
        charters=charters,
        budget=budget,
        require_certify=policy.termination.consensus_requires_adversary_certify,
        quorum_min=policy.run.quorum_min_operators,
        compaction=policy.run.compaction.model_dump(),
        panel_note=note,
    )

    result = asyncio.run(engine.run(args.task))

    now = _dt.datetime.now()
    out = run_dir(args.out or policy.output.dir, args.task, now)
    paths = emit(result, out, now)

    print(f"panel: {note}")
    print(f"rounds: {result.rounds_run}  stop: {result.stop_reason}")
    if result.unavailable:
        print(f"unavailable: {', '.join(result.unavailable)}")
    print(f"artifact : {paths['final_artifact']}")
    print(f"transcript: {paths['transcript']}")
    print(f"report   : {paths['run_report']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="warroom", description="Multi-operator AI war room.")
    p.add_argument("--operators", default="operators.yaml", help="path to operators.yaml")
    p.add_argument("--policy", default="warroom.yaml", help="path to warroom.yaml")
    p.add_argument("--panel", choices=["config", "fake"], default="config",
                   help="'fake' forces every operator to the process-free fake adapter")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="validate config + health-check the panel")
    d.set_defaults(func=cmd_doctor)

    r = sub.add_parser("run", help="run the war room on a task")
    r.add_argument("task", help="the task/spec for the panel")
    r.add_argument("--out", default=None, help="override output dir template")
    r.set_defaults(func=cmd_run)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # fail loud, but readable
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
