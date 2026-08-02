"""Transcript marshaling, verbatim-artifact guarantee, and compaction."""
from warroom.adapters.base import Phase, Role, Status, TurnResult, Usage
from warroom.engine.transcript import Transcript


def _res(role, name, content):
    return TurnResult(operator_name=name, role=role, content=content, status=Status.OK, usage=Usage())


def test_marshal_includes_artifact_verbatim_and_attribution():
    t = Transcript()
    t.set_artifact("THE ARTIFACT BODY")
    t.append(_res(Role.ADVERSARY, "gpt-sol", "objection X"), round_no=1, phase=Phase.CRITIQUE)
    rendered = t.marshal_for(Role.ARCHITECT)
    assert "THE ARTIFACT BODY" in rendered
    assert "ADVERSARY (gpt-sol)" in rendered
    assert "objection X" in rendered


def test_jsonl_roundtrip(tmp_path):
    t = Transcript()
    t.append(_res(Role.LOCAL, "qwen", "note"), round_no=1, phase=Phase.CRITIQUE)
    p = tmp_path / "transcript.jsonl"
    t.write_jsonl(p)
    back = Transcript.read_jsonl(p)
    assert len(back.turns) == 1
    assert back.turns[0].content == "note"


def test_compaction_folds_old_discussion_but_not_artifact():
    t = Transcript()
    t.set_artifact("KEEP ME VERBATIM")
    # two old rounds + one recent
    t.append(_res(Role.ADVERSARY, "gpt", "r1 objection"), round_no=1, phase=Phase.CRITIQUE)
    t.append(_res(Role.LOCAL, "qwen", "r1 note"), round_no=1, phase=Phase.CRITIQUE)
    t.append(_res(Role.ADVERSARY, "gpt", "r2 objection"), round_no=2, phase=Phase.CRITIQUE)

    calls = {}

    def fake_summarize(text):
        calls["text"] = text
        return "SUMMARY OF ROUND 1"

    t.compact(fake_summarize, keep_recent_rounds=1)
    rendered = t.marshal_for(Role.ARCHITECT)
    assert "KEEP ME VERBATIM" in rendered          # artifact untouched
    assert "SUMMARY OF ROUND 1" in rendered         # old rounds folded
    assert "r1 objection" in calls["text"]          # summarizer saw the old text
    assert "r2 objection" in rendered               # recent round retained
