"""Config schema + fourth-slot resolution."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from warroom.adapters.base import Role
from warroom.config.loader import load_operators, load_run_policy, resolve_fourth
from warroom.config.models import HttpConfig, OperatorsFile

REPO = Path(__file__).resolve().parents[1]


def test_repo_configs_load():
    spec = load_operators(REPO / "operators.yaml")
    policy = load_run_policy(REPO / "warroom.yaml")
    assert policy.run.max_rounds == 3
    roles = {op.role for op in spec.operators.values()}
    assert Role.ARCHITECT in roles and Role.ADVERSARY in roles and Role.LOCAL in roles


def test_fourth_off_by_default():
    spec = load_operators(REPO / "operators.yaml")
    panel, note = resolve_fourth(spec)
    assert "fourth" not in panel
    assert "OFF" in note


def test_fourth_cloud_variant_resolves():
    spec = load_operators(REPO / "operators.yaml")
    spec.fourth.enabled = True
    spec.fourth.variant = "cloud_api"
    panel, note = resolve_fourth(spec)
    assert "fourth" in panel
    assert panel["fourth"].role is Role.FOURTH
    assert panel["fourth"].http.metered is True
    assert "ON" in note and "cloud_api" in note


def test_fourth_second_gpu_variant_resolves():
    spec = load_operators(REPO / "operators.yaml")
    spec.fourth.enabled = True
    spec.fourth.variant = "second_gpu"
    panel, _ = resolve_fourth(spec)
    assert panel["fourth"].http.local is True
    assert panel["fourth"].http.metered is False


def test_metered_requires_price_table():
    with pytest.raises(ValidationError):
        HttpConfig(base_url="https://x/v1", metered=True)  # no price_per_mtok


def test_panel_must_have_architect():
    with pytest.raises(ValidationError):
        OperatorsFile.model_validate(
            {
                "operators": {
                    "a": {
                        "role": "adversary",
                        "adapter": "http_openai",
                        "model": "m",
                        "http": {"base_url": "http://x/v1"},
                    }
                }
            }
        )
