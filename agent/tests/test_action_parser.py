"""Tests for ActionParser — LLM output parsing and junk-stripping."""

import pytest
from action_parser import ActionParser


@pytest.fixture
def parser():
    return ActionParser()


# ── Clean JSON ────────────────────────────────────────────────────────────────


def test_clean_json(parser):
    result = parser.parse('{"action":"explore","reason":"looks good"}')
    assert result == {"action": "explore", "reason": "looks good"}


def test_missing_reason_defaults(parser):
    result = parser.parse('{"action":"idle"}')
    assert result["action"] == "idle"
    assert result["reason"] == "no reason given"


def test_numeric_action_rejected_as_idle(parser):
    # Numeric action values are invalid LLM output — should fall back to idle
    result = parser.parse('{"action": 42, "reason": "test"}')
    assert result["action"] == "idle"


# ── Junk characters emitted by small LLMs ────────────────────────────────────


def test_trailing_paren_before_brace(parser):
    # Exact pattern seen in logs: ..."nearby.")}
    raw = '{"action":"explore","reason":"new resources nearby.")}'
    result = parser.parse(raw)
    assert result["action"] == "explore"
    assert "nearby" in result["reason"]


def test_trailing_semicolon(parser):
    result = parser.parse('{"action":"idle","reason":"done"};')
    assert result["action"] == "idle"


def test_trailing_dot_before_brace(parser):
    result = parser.parse('{"action":"gather_resource","reason":"need wood".}')
    assert result["action"] == "gather_resource"


def test_trailing_comma_before_brace(parser):
    result = parser.parse('{"action":"explore","reason":"ok",}')
    assert result["action"] == "explore"


# ── JSON embedded in surrounding text ────────────────────────────────────────


def test_json_in_prose(parser):
    raw = 'Sure! Here is my action: {"action":"chop_tree","reason":"have axe"} hope that helps'
    result = parser.parse(raw)
    assert result["action"] == "chop_tree"


def test_json_with_leading_newlines(parser):
    result = parser.parse('\n\n{"action":"explore","reason":"scouting"}')
    assert result["action"] == "explore"


# ── Fallback / error cases ────────────────────────────────────────────────────


def test_none_input_returns_idle(parser):
    result = parser.parse(None)
    assert result["action"] == "idle"


def test_empty_string_returns_idle(parser):
    result = parser.parse("")
    assert result["action"] == "idle"


def test_totally_malformed_returns_idle(parser):
    result = parser.parse("I recommend you explore the map!")
    assert result["action"] == "idle"


def test_no_action_key_returns_idle(parser):
    result = parser.parse('{"reason":"something","goal":"survive"}')
    assert result["action"] == "idle"


# ── Extra fields are forwarded ────────────────────────────────────────────────


def test_extra_target_field_forwarded(parser):
    raw = '{"action":"eat_food:berries","reason":"hungry","target":"berries"}'
    result = parser.parse(raw)
    assert result["action"] == "eat_food:berries"
    assert result["target"] == "berries"


def test_extra_direction_field_forwarded(parser):
    raw = '{"action":"explore","reason":"scouting","direction":"north"}'
    result = parser.parse(raw)
    assert result["direction"] == "north"


def test_only_action_and_reason_not_duplicated(parser):
    raw = '{"action":"idle","reason":"nothing to do"}'
    result = parser.parse(raw)
    assert set(result.keys()) == {"action", "reason"}
