"""Verdict parsing and GATE decisions."""
from warroom.engine.termination import decide, parse_verdict


def test_parse_verdict_certified():
    content = 'ok\n```verdict\n{"certify": true, "objections": []}\n```'
    v = parse_verdict(content)
    assert v.certify is True and v.raw_found is True


def test_parse_verdict_missing_is_not_certified():
    v = parse_verdict("no verdict block here")
    assert v.certify is False and v.raw_found is False


def test_parse_verdict_malformed_json_is_not_certified():
    v = parse_verdict("```verdict\n{not json}\n```")
    assert v.certify is False and v.raw_found is False


def test_consensus_requires_certify_and_stable_artifact():
    certified = '```verdict\n{"certify": true, "objections": []}\n```'
    d = decide(
        round_no=2, max_rounds=3, adversary_content=certified,
        architect_changed=False, budget_exhausted=False, budget_reason="",
        quorum_ok=True,
    )
    assert d.stop and "consensus" in d.reason


def test_certified_but_changed_does_not_consense():
    certified = '```verdict\n{"certify": true}\n```'
    d = decide(
        round_no=1, max_rounds=3, adversary_content=certified,
        architect_changed=True, budget_exhausted=False, budget_reason="",
        quorum_ok=True,
    )
    assert not d.stop


def test_max_rounds_stops():
    d = decide(
        round_no=3, max_rounds=3, adversary_content=None,
        architect_changed=True, budget_exhausted=False, budget_reason="",
        quorum_ok=True,
    )
    assert d.stop and "max_rounds" in d.reason


def test_budget_stops_first():
    d = decide(
        round_no=1, max_rounds=3, adversary_content=None,
        architect_changed=True, budget_exhausted=True, budget_reason="cost",
        quorum_ok=True,
    )
    assert d.stop and "budget" in d.reason


def test_lost_quorum_stops():
    d = decide(
        round_no=1, max_rounds=3, adversary_content=None,
        architect_changed=True, budget_exhausted=False, budget_reason="",
        quorum_ok=False,
    )
    assert d.stop and "quorum" in d.reason
