"""Emit the run's artifacts: transcript.jsonl, final_artifact.md, run_report.md.

Timestamps are stamped *here* (not inside the engine) so the engine stays
deterministic and reproducible.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import List

from .engine.round_engine import RunResult


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:max_len] or "run").strip("-")


def run_dir(template: str, task: str, now: _dt.datetime | None = None) -> Path:
    now = now or _dt.datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    return Path(template.format(timestamp=stamp, slug=slugify(task)))


def _render_report(result: RunResult, now: _dt.datetime) -> str:
    lines: List[str] = [
        "# Warroom run report",
        "",
        f"- when: {now.isoformat(timespec='seconds')}",
        f"- task: {result.task}",
        f"- rounds run: {result.rounds_run}",
        f"- stop reason: {result.stop_reason}",
        f"- panel: {result.panel_note}",
        f"- budget-truncated: {result.truncated}",
    ]
    if result.unavailable:
        lines.append(f"- unavailable operators: {', '.join(result.unavailable)}")
    b = result.budget
    lines += [
        "",
        "## Budget",
        f"- spent: ${b['spent_usd']:.4f}",
        f"- tokens: {b['input_tokens']} in / {b['output_tokens']} out",
        f"- elapsed: {b['elapsed_s']}s",
    ]
    if b.get("reasons"):
        lines.append(f"- limit notes: {'; '.join(b['reasons'])}")
    lines += ["", "## Turns", ""]
    for t in result.transcript.turns:
        lines.append(f"- r{t.round_no} · {t.role} ({t.operator}) · {t.phase}")
    return "\n".join(lines) + "\n"


def emit(result: RunResult, out_dir: Path, now: _dt.datetime | None = None) -> dict:
    now = now or _dt.datetime.now()
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = out_dir / "transcript.jsonl"
    result.transcript.write_jsonl(transcript_path)

    artifact_path = out_dir / "final_artifact.md"
    artifact_path.write_text(result.final_artifact.strip() + "\n", encoding="utf-8")

    report_path = out_dir / "run_report.md"
    report_path.write_text(_render_report(result, now), encoding="utf-8")

    return {
        "transcript": str(transcript_path),
        "final_artifact": str(artifact_path),
        "run_report": str(report_path),
    }
