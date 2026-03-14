"""Tests for goal completion and removal from prompt output."""

from models.state import GameState
from goals.manager import GoalManager


def test_incomplete_goals_appear_in_prompt():
    """Goals that are not complete should appear in the prompt."""
    gm = GoalManager()

    state_autumn = GameState(
        day=1,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x10"],
        equipped=None,
        position={"x": 0, "z": 0},
    )

    prompt = gm.format_for_prompt(state_autumn, {"log": 10})

    # All goals should be present during normal gameplay
    assert "Long-term (Autumn):" in prompt
    assert "Mid-term" in prompt
    assert "Short-term" in prompt or "Stable" in prompt


def test_completed_long_term_goal_removed_from_prompt():
    """When season changes and a new long-term goal starts, old one is removed."""
    gm = GoalManager()

    # Autumn goal (completes when winter arrives)
    state_autumn = GameState(
        day=15,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
    )

    autumn_goal = gm.get_long_term_goal(state_autumn)

    # During autumn, goal should be incomplete
    assert autumn_goal.goal_check is not None
    assert autumn_goal.goal_check(state_autumn) is False

    prompt_autumn = gm.format_for_prompt(state_autumn, {})
    assert "Long-term (Autumn):" in prompt_autumn

    # Winter arrives - autumn goal is now complete, should be hidden
    # The new winter goal is shown instead (which is incomplete)
    state_winter = GameState(
        day=20,
        time_of_day=0.5,
        phase="day",
        season="winter",
        health=100,
        hunger=100,
        sanity=100,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
    )

    winter_goal = gm.get_long_term_goal(state_winter)

    # Winter goal should be incomplete
    assert winter_goal.goal_check is not None
    assert winter_goal.goal_check(state_winter) is False

    prompt_winter = gm.format_for_prompt(state_winter, {})
    assert "Long-term (Winter):" in prompt_winter
    assert "Long-term (Autumn):" not in prompt_winter


def test_all_seasons_show_goals_during_their_season():
    """All four seasons should show their goals when active."""
    gm = GoalManager()
    seasons = ["autumn", "winter", "spring", "summer"]

    for season in seasons:
        state = GameState(
            day=10,
            time_of_day=0.5,
            phase="day",
            season=season,
            health=100,
            hunger=100,
            sanity=100,
            inventory=[],
            equipped=None,
            position={"x": 0, "z": 0},
        )

        prompt = gm.format_for_prompt(state, {})

        # During the season, goal should appear
        assert f"Long-term ({season.capitalize()}):" in prompt


def test_prompt_structure_with_active_goals():
    """Verify the format structure for active (incomplete) goals."""
    gm = GoalManager()

    state = GameState(
        day=5,
        time_of_day=0.5,
        phase="day",
        season="spring",
        health=80,
        hunger=90,
        sanity=85,
        inventory=["log x5", "grass x10"],
        equipped=None,
        position={"x": 0, "z": 0},
    )

    prompt = gm.format_for_prompt(state, {"log": 5, "grass": 10})

    # Should have long-term, mid-term, short-term (or stable)
    assert "Long-term (Spring):" in prompt
    assert "Mid-term" in prompt  # Just check it exists, format varies
    assert "Short-term" in prompt or "Stable" in prompt


def test_all_seasons_show_completion_correctly():
    """All four seasons should show completion status appropriately."""
    gm = GoalManager()
    seasons = ["autumn", "winter", "spring", "summer"]

    for season in seasons:
        state = GameState(
            day=10,
            time_of_day=0.5,
            phase="day",
            season=season,
            health=100,
            hunger=100,
            sanity=100,
            inventory=[],
            equipped=None,
            position={"x": 0, "z": 0},
        )

        prompt = gm.format_for_prompt(state, {})

        # During the season, goal should not show complete
        assert "✓ COMPLETE" not in prompt
        assert f"Long-term ({season.capitalize()}):" in prompt
