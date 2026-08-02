"""End-to-end engine run against the process-free fake panel.

Proves the whole loop converges via the ADVERSARY-driven consensus gate (round 2,
before the round cap) — not merely by exhausting max_rounds.
"""
from pathlib import Path

import pytest

from warroom.adapters.base import Role
from warroom.engine.budget import Budget
from warroom.engine.round_engine import RoundEngine
from warroom.report import emit, run_dir
from warroom.testing.fake_adapter import FakeAdapter


def _panel():
    return {
        "architect": FakeAdapter("architect", Role.ARCHITECT),
        "adversary": FakeAdapter("adversary", Role.ADVERSARY),
        "local": FakeAdapter("local", Role.LOCAL),
    }


def _budget():
    return Budget(max_rounds=3, max_wall_clock_s=60, max_cost_usd=1.0, per_turn_token_cap=24000)


@pytest.mark.asyncio
async def test_run_converges_on_consensus():
    engine = RoundEngine(panel=_panel(), charters={}, budget=_budget(), quorum_min=2)
    result = await engine.run("Design a widget")
    assert result.rounds_run == 2
    assert "consensus" in result.stop_reason
    assert "FINAL DRAFT" in result.final_artifact
    assert "Change log" in result.final_artifact
    assert not result.truncated


@pytest.mark.asyncio
async def test_run_degrades_when_adversary_unavailable():
    panel = _panel()
    # Remove the adversary -> only architect + local remain; quorum(2) still holds,
    # but with no adversary to certify, the run rides to the max_rounds cap.
    del panel["adversary"]
    engine = RoundEngine(panel=panel, charters={}, budget=_budget(), quorum_min=2)
    result = await engine.run("Design a widget")
    assert "max_rounds" in result.stop_reason
    assert result.final_artifact.strip()


@pytest.mark.asyncio
async def test_emit_writes_three_artifacts(tmp_path):
    engine = RoundEngine(panel=_panel(), charters={}, budget=_budget(), quorum_min=2)
    result = await engine.run("Design a widget")
    out = tmp_path / "run"
    paths = emit(result, out)
    for key in ("transcript", "final_artifact", "run_report"):
        assert Path(paths[key]).exists()
    assert "consensus" in Path(paths["run_report"]).read_text()
