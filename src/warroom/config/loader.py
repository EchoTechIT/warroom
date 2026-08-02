"""Load, validate, and resolve Warroom configuration.

``resolve_fourth`` collapses the 4th-slot ``variant`` indirection into a plain
enabled/disabled operator, so everything downstream sees a uniform panel.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import yaml

from ..adapters.base import Role
from .models import OperatorConfig, OperatorsFile, WarroomFile


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the top level")
    return data


def load_operators(path: str | Path) -> OperatorsFile:
    return OperatorsFile.model_validate(_read_yaml(Path(path)))


def load_run_policy(path: str | Path) -> WarroomFile:
    return WarroomFile.model_validate(_read_yaml(Path(path)))


def resolve_fourth(spec: OperatorsFile) -> Tuple[Dict[str, OperatorConfig], str]:
    """Return the effective panel (name -> OperatorConfig) with the fourth slot
    resolved, plus a human-readable note about the fourth slot's state.

    The fourth operator is spliced in under the key ``"fourth"`` only when it is
    enabled and its mode is not ``off``; otherwise it is omitted entirely.
    """
    panel: Dict[str, OperatorConfig] = {
        name: op for name, op in spec.operators.items() if op.enabled
    }

    f = spec.fourth
    if not f.enabled or f.mode == "off":
        return panel, f"fourth slot: OFF (mode={f.mode}, enabled={f.enabled})"

    chosen = f.variants[f.variant].model_copy(update={"role": Role.FOURTH})
    if not chosen.enabled:
        return panel, f"fourth slot: variant {f.variant!r} present but disabled"

    panel["fourth"] = chosen
    return panel, f"fourth slot: ON (mode={f.mode}, variant={f.variant})"
