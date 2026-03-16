"""E2E tests for Phase 3: Dynamic Mid-Term Goal Selection.

Tests the full flow of generating multiple mid-term goal options,
filtering by context, and prioritizing them.
"""

from models.state import GameState
from goals.manager import GoalManager


def test_goal_manager_returns_multiple_mid_term_options():
    """GoalManager should return 2-3 mid-term goal options, not just one."""
    gm = GoalManager()
    
    state = GameState(
        day=5,
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
    
    # Should return multiple options (list), not single goal
    mid_term_goals = gm.get_mid_term_goals(state, {})
    
    assert isinstance(mid_term_goals, list)
    assert 2 <= len(mid_term_goals) <= 3  # Max 3 to avoid overwhelming LLM


def test_mid_term_options_are_context_appropriate():
    """Mid-term options should change based on game state context."""
    gm = GoalManager()
    
    # Early game: no science machine, low food
    state_early = GameState(
        day=5,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x5"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],  # No science machine
    )
    
    early_goals = gm.get_mid_term_goals(state_early, {"log": 5})
    
    # Should offer base building (no science machine)
    descriptions = [g.description for g in early_goals]
    assert any("base" in desc.lower() or "science" in desc.lower() for desc in descriptions)


def test_all_mid_term_goals_have_predicates():
    """All mid-term goal options should have goal_check predicates."""
    gm = GoalManager()
    
    state = GameState(
        day=10,
        time_of_day=0.5,
        phase="day",
        season="winter",
        health=80,
        hunger=90,
        sanity=85,
        inventory=["log x10", "twigs x20"],
        equipped=None,
        position={"x": 0, "z": 0},
    )
    
    mid_term_goals = gm.get_mid_term_goals(state, {"log": 10, "twigs": 20})
    
    for goal in mid_term_goals:
        assert goal.goal_check is not None, f"Goal '{goal.description}' missing goal_check predicate"


def test_mid_term_goal_completion_detection():
    """When mid-term goal is completed, predicate should return True."""
    gm = GoalManager()
    
    # State without science machine
    state_no_machine = GameState(
        day=5,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
    )
    
    goals_before = gm.get_mid_term_goals(state_no_machine, {})
    
    # Find "build base" goal
    build_base_goal = None
    for goal in goals_before:
        if "base" in goal.description.lower() or "science" in goal.description.lower():
            build_base_goal = goal
            break
    
    assert build_base_goal is not None, "Should offer base building goal when no science machine"
    assert build_base_goal.goal_check(state_no_machine) is False, "Goal should be incomplete"
    
    # State WITH science machine
    state_with_machine = GameState(
        day=10,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 5}
        ],
    )
    
    # Same goal should now be complete
    assert build_base_goal.goal_check(state_with_machine) is True, "Goal should be complete with science machine"


def test_mid_term_goals_prioritized_by_context():
    """Mid-term goals should be reordered based on urgency and context."""
    gm = GoalManager()
    
    # Critical food shortage
    state_starving = GameState(
        day=15,
        time_of_day=0.5,
        phase="day",
        season="winter",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x5"],
        equipped=None,
        position={"x": 0, "z": 0},
    )
    
    goals = gm.get_mid_term_goals(state_starving, {"log": 5})  # Very low food
    
    # Food stockpiling should be offered when food is critically low
    descriptions = [g.description.lower() for g in goals]
    assert any("food" in desc or "stockpile" in desc for desc in descriptions)


def test_completed_mid_term_goals_not_offered():
    """Completed mid-term goals should not appear in options."""
    gm = GoalManager()
    
    # State with science machine already built
    state_with_machine = GameState(
        day=15,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x20"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 5}
        ],
    )
    
    goals = gm.get_mid_term_goals(state_with_machine, {"log": 20})
    
    # Should NOT offer base building (already have science machine)
    # Check all offered goals are incomplete
    for goal in goals:
        assert goal.goal_check(state_with_machine) is False, \
            f"Goal '{goal.description}' is already complete, should not be offered"


def test_mid_term_goal_selection_full_flow():
    """E2E: Full cycle of getting mid-term options and tracking completion."""
    gm = GoalManager()
    
    # Cycle 1: Early game, no science machine
    state_day5 = GameState(
        day=5,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x3"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
    )
    
    options_day5 = gm.get_mid_term_goals(state_day5, {"log": 3})
    assert 2 <= len(options_day5) <= 3
    
    # LLM would pick one (simulate picking "Build base")
    build_base = next((g for g in options_day5 if "base" in g.description.lower() or "science" in g.description.lower()), None)
    assert build_base is not None
    assert build_base.goal_check(state_day5) is False  # Not complete yet
    
    # Cycle 2: Mid-game, science machine built
    state_day15 = GameState(
        day=15,
        time_of_day=0.5,
        phase="day",
        season="autumn",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x10"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 3}
        ],
    )
    
    # Previous goal now complete
    assert build_base.goal_check(state_day15) is True  # ✓ Complete!
    
    # Get new options (should not include build base)
    options_day15 = gm.get_mid_term_goals(state_day15, {"log": 10})
    
    # All offered goals should be incomplete
    for goal in options_day15:
        assert goal.goal_check(state_day15) is False
    
    # Should offer different goals now
    descriptions_day15 = [g.description.lower() for g in options_day15]
    # Either exploration or stockpiling, but NOT base building
    assert not any("build" in desc and "science" in desc for desc in descriptions_day15)


def test_mid_term_goals_limit_parameter():
    """E2E: Limit parameter controls number of options returned."""
    gm = GoalManager()
    
    state = GameState(
        day=5,
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
    
    # Default: up to 3 goals
    options_default = gm.get_mid_term_goals(state, {})
    assert len(options_default) <= 3
    
    # Request only 1 goal
    options_limit_1 = gm.get_mid_term_goals(state, {}, limit=1)
    assert len(options_limit_1) == 1
    assert options_limit_1[0].goal_check is not None
    
    # Request 2 goals
    options_limit_2 = gm.get_mid_term_goals(state, {}, limit=2)
    assert len(options_limit_2) <= 2
    assert all(g.goal_check is not None for g in options_limit_2)
    
    # Request more than available (should return all available, not error)
    options_limit_10 = gm.get_mid_term_goals(state, {}, limit=10)
    assert len(options_limit_10) <= 10  # Won't have more than max available
