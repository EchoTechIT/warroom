"""Golden parse tests — the tripwire for CLI output-format drift."""
from warroom.adapters.base import Role, Status
from warroom.adapters.cli_claude_code import ClaudeCodeAdapter
from warroom.adapters.cli_codex import CodexAdapter
from warroom.config.models import CliConfig


def _claude():
    return ClaudeCodeAdapter(
        "architect", Role.ARCHITECT, "claude-fable-5",
        CliConfig(command=["claude"], base_args=["-p"]),
    )


def _codex():
    return CodexAdapter(
        "adversary", Role.ADVERSARY, "gpt-sol",
        CliConfig(command=["codex", "exec"], sandbox="read-only"),
    )


CLAUDE_STREAM = "\n".join([
    '{"type":"system","subtype":"init"}',
    '{"type":"assistant","message":{"content":[{"type":"text","text":"Hello "}]}}',
    '{"type":"assistant","message":{"content":[{"type":"text","text":"world"}]}}',
    '{"type":"result","usage":{"input_tokens":11,"output_tokens":7}}',
])


def test_claude_stream_json_parses_text_and_usage():
    r = _claude().parse(CLAUDE_STREAM, "", 0)
    assert r.status is Status.OK
    assert r.content == "Hello world"
    assert r.usage.input_tokens == 11 and r.usage.output_tokens == 7
    assert r.usage.metered is False


def test_claude_nonzero_exit_no_output_is_unavailable():
    r = _claude().parse("", "rate limit reached", 1)
    assert r.status is Status.UNAVAILABLE


def test_claude_empty_when_no_text():
    r = _claude().parse('{"type":"system"}', "", 0)
    assert r.status is Status.EMPTY


def test_codex_json_line_parses():
    out = 'log line\n{"message":"my critique","usage":{"input_tokens":3,"output_tokens":4}}'
    r = _codex().parse(out, "", 0)
    assert r.status is Status.OK
    assert r.content == "my critique"
    assert r.usage.output_tokens == 4


def test_codex_plain_text_fallback():
    r = _codex().parse("just a plain critique with no json", "", 0)
    assert r.status is Status.OK
    assert "plain critique" in r.content


def test_codex_nonzero_exit_no_output_is_unavailable():
    r = _codex().parse("", "not logged in", 1)
    assert r.status is Status.UNAVAILABLE
