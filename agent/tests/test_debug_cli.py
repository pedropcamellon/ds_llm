"""
test_debug_cli.py — Tests for offline debug CLI.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from debug_cli import main, _state_summary


# Path to fixtures relative to agent/ directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_fixtures_exist():
    """Verify all required fixture files exist."""
    required = [
        "day1_fresh.json",
        "night_no_fire.json",
        "low_health_hostile.json",
        "winter_stocked.json",
    ]
    for fixture in required:
        assert (FIXTURES_DIR / fixture).exists(), f"Missing fixture: {fixture}"


@pytest.mark.parametrize(
    "fixture",
    [
        "day1_fresh.json",
        "night_no_fire.json",
        "low_health_hostile.json",
        "winter_stocked.json",
    ],
)
def test_load_fixture_no_exceptions(fixture, capsys):
    """Each fixture loads and processes without exceptions."""
    fixture_path = FIXTURES_DIR / fixture
    with patch("sys.argv", ["debug_cli.py", str(fixture_path), "--actions-only"]):
        result = main()
    assert result == 0, f"Failed to process {fixture}"
    captured = capsys.readouterr()
    assert captured.out, f"No output for {fixture}"


@pytest.mark.parametrize(
    "fixture",
    [
        "day1_fresh.json",
        "night_no_fire.json",
        "low_health_hostile.json",
        "winter_stocked.json",
    ],
)
def test_fixture_produces_concrete_actions(fixture, capsys):
    """Each fixture produces a non-empty concrete actions list."""
    fixture_path = FIXTURES_DIR / fixture
    with patch("sys.argv", ["debug_cli.py", str(fixture_path), "--actions-only"]):
        main()
    captured = capsys.readouterr()
    # Should have at least "explore" or other actions
    assert captured.out.strip(), f"No actions output for {fixture}"
    # Check for action-like content (not just headers)
    lines = [ln.strip() for ln in captured.out.split("\n") if ln.strip()]
    action_lines = [ln for ln in lines if not ln.startswith("[")]
    assert len(action_lines) > 0, f"No concrete actions for {fixture}"


def test_night_no_fire_produces_fire_goal(capsys):
    """night_no_fire.json should produce a fire-related short-term goal."""
    fixture_path = FIXTURES_DIR / "night_no_fire.json"
    with patch("sys.argv", ["debug_cli.py", str(fixture_path)]):
        main()
    captured = capsys.readouterr()
    output_lower = captured.out.lower()
    # Should mention fire, campfire, or torch in goals section
    assert any(
        word in output_lower for word in ["fire", "campfire", "torch", "light"]
    ), "No fire-related goal for night_no_fire.json"


def test_json_output_flag_produces_valid_json(capsys):
    """--json flag produces parseable JSON with expected keys."""
    fixture_path = FIXTURES_DIR / "day1_fresh.json"
    with patch("sys.argv", ["debug_cli.py", str(fixture_path), "--json"]):
        result = main()
    assert result == 0
    captured = capsys.readouterr()
    output_json = json.loads(captured.out)
    
    # Check expected top-level keys
    assert "state_summary" in output_json
    assert "goals" in output_json
    assert "concrete_actions" in output_json
    assert "prompt" in output_json
    
    # Verify types
    assert isinstance(output_json["concrete_actions"], list)
    assert isinstance(output_json["prompt"], str)


def test_actions_only_flag_excludes_prompt(capsys):
    """--actions-only output should not include prompt text."""
    fixture_path = FIXTURES_DIR / "day1_fresh.json"
    with patch("sys.argv", ["debug_cli.py", str(fixture_path), "--actions-only"]):
        main()
    captured = capsys.readouterr()
    output_lower = captured.out.lower()
    
    # Should have actions header
    assert "[concrete actions]" in output_lower
    # Should NOT have prompt-related content
    assert "[full prompt]" not in output_lower
    assert "survive in the wild" not in output_lower  # common prompt preamble


def test_prompt_only_flag_shows_only_prompt(capsys):
    """--prompt-only output should contain only the prompt text."""
    fixture_path = FIXTURES_DIR / "day1_fresh.json"
    with patch("sys.argv", ["debug_cli.py", str(fixture_path), "--prompt-only"]):
        main()
    captured = capsys.readouterr()
    output_lower = captured.out.lower()
    
    # Should NOT have section headers
    assert "[state summary]" not in output_lower
    assert "[concrete actions]" not in output_lower
    # Should have prompt content
    assert "survive" in output_lower or "action" in output_lower


def test_state_summary_formatting():
    """_state_summary produces expected format."""
    state = {
        "day": 5,
        "season": "autumn",
        "phase": "day",
        "time_of_day": 0.42,
        "health": 120,
        "hunger": 85,
        "sanity": 140,
        "temperature": 18,
        "is_raining": False,
        "inventory": ["log x10", "twigs x5"],
        "equipped": "axe",
        "nearby_entities": [{"name": "tree"}] * 12,
        "threats": [],
    }
    summary = _state_summary(state)
    
    assert "Day 5" in summary
    assert "autumn" in summary
    assert "Health: 120" in summary
    assert "axe" in summary
    assert "Nearby entities: 12" in summary


def test_low_health_hostile_has_critical_urgency(capsys):
    """low_health_hostile.json should trigger CRITICAL urgency due to health < 50."""
    fixture_path = FIXTURES_DIR / "low_health_hostile.json"
    with patch("sys.argv", ["debug_cli.py", str(fixture_path)]):
        main()
    captured = capsys.readouterr()
    output_lower = captured.out.lower()
    
    # Should mention critical or urgent
    assert "critical" in output_lower or "urgent" in output_lower
    # Should have health-related goal
    assert "health" in output_lower or "heal" in output_lower or "eat" in output_lower
