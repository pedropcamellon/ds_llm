"""E2E test: Goal completion detection through full goal manager flow.

Tests the complete flow: game state → goal manager → goal with predicate → completion check.
This demonstrates "small wins" — goals can now detect their own completion.
"""

from models.state import GameState
from goals.manager import GoalManager


def test_long_term_goal_completed_when_season_changes():
    """Long-term goal should be marked complete when season transitions.

    SCENARIO:
    - Autumn day 15: preparing for winter
    - Goal: "Survive autumn, reach winter"
    - Winter day 17: season changed!
    - Result: Autumn goal is now COMPLETE ✓
    """
    gm = GoalManager()

    # Day 15 of autumn — winter approaching
    state_autumn = GameState(
        health=100, hunger=100, sanity=200, phase="day", season="autumn", day=15
    )

    autumn_goal = gm.get_long_term_goal(state_autumn)

    # Verify we got the autumn goal
    assert autumn_goal.season == "autumn"
    assert autumn_goal.goal_check is not None

    # Goal should NOT be complete yet (still autumn)
    assert autumn_goal.goal_check(state_autumn) is False

    # --- SEASON CHANGE ---
    # Day 17: winter has arrived!
    state_winter = GameState(
        health=100, hunger=100, sanity=200, phase="day", season="winter", day=17
    )

    # NOW the autumn goal should be complete
    assert autumn_goal.goal_check(state_winter) is True

    # And we get a new winter goal
    winter_goal = gm.get_long_term_goal(state_winter)
    
    assert winter_goal.season == "winter"
    assert winter_goal.goal_check is not None
    assert winter_goal.goal_check(state_winter) is False  # Not complete yet


def test_goal_completion_visible_in_prompt():
    """Goal completion can be checked before building prompt.

    SCENARIO:
    This shows how the agent loop could check goal completion
    and display a visible "GOAL COMPLETED" message.
    """
    gm = GoalManager()

    # Autumn day 16 (last day)
    state_autumn = GameState(
        health=100, hunger=100, sanity=200, phase="day", season="autumn", day=16
    )

    autumn_goal = gm.get_long_term_goal(state_autumn)

    # Simulate agent loop checking goal
    if autumn_goal.goal_check and autumn_goal.goal_check(state_autumn):
        completion_msg = f"🎉 GOAL COMPLETED: {autumn_goal.description}"
    else:
        completion_msg = None

    assert completion_msg is None  # Still in autumn

    # --- Next cycle: winter arrives ---
    state_winter = GameState(
        health=100, hunger=100, sanity=200, phase="day", season="winter", day=17
    )

    # Check again (using same goal object)
    if autumn_goal.goal_check and autumn_goal.goal_check(state_winter):
        completion_msg = "Goal completed!"
    else:
        completion_msg = None

    assert completion_msg is not None


def test_all_seasons_have_goal_completion_predicates():
    """Every season should have a goal_check predicate defined."""
    gm = GoalManager()

    seasons = ["autumn", "winter", "spring", "summer"]

    for season in seasons:
        state = GameState(
            health=100, hunger=100, sanity=200, phase="day", season=season, day=1
        )

        goal = gm.get_long_term_goal(state)

        # Every season goal should have a predicate
        assert goal.goal_check is not None, f"{season} goal missing goal_check"

        # Goal should NOT be complete in its own season
        assert goal.goal_check(state) is False, f"{season} goal already complete?"


def test_winter_to_spring_goal_transition():
    """Complete E2E flow: Winter → Spring transition with goal completion."""
    gm = GoalManager()

    # Winter day 30 — spring approaching
    state_winter = GameState(
        health=80,
        hunger=60,
        sanity=150,
        phase="dusk",
        season="winter",
        day=30,
        temperature=-5,
    )

    winter_goal = gm.get_long_term_goal(state_winter)
    assert winter_goal.season == "winter"
    assert winter_goal.goal_check is not None

    # Not complete yet
    assert winter_goal.goal_check(state_winter) is False

    # Spring arrives!
    state_spring = GameState(
        health=80,
        hunger=60,
        sanity=150,
        phase="day",
        season="spring",
        day=33,
        temperature=15,
    )

    # Winter goal is now complete
    assert winter_goal.goal_check(state_spring) is True

    # Get spring goal
    spring_goal = gm.get_long_term_goal(state_spring)
    assert spring_goal.season == "spring"
    assert spring_goal.goal_check is not None

    # Spring goal not complete yet
    assert spring_goal.goal_check(state_spring) is False


def test_format_for_prompt_with_goal_completion():
    """Goal completion can be integrated into prompt formatting.

    DEMO: Shows how completion status could appear in LLM prompt.
    """
    gm = GoalManager()

    state_winter = GameState(
        health=100, hunger=100, sanity=200, phase="day", season="winter", day=20
    )

    winter_goal = gm.get_long_term_goal(state_winter)

    # Build prompt with completion status
    prompt = gm.format_for_prompt(state_winter, inv={})

    # Add completion indicator (this is what agent could do)
    if winter_goal.goal_check and winter_goal.goal_check(state_winter):
        status_line = "[✓ COMPLETE]"
    else:
        status_line = "[In Progress]"

    # Verify prompt was generated
    assert len(prompt) > 0
    assert winter_goal.season == "winter"

    # Status would be "In Progress" since still in winter
    assert status_line == "[In Progress]"
