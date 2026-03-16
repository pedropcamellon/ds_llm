"""Unit tests for Phase 3: Mid-Term Goal Generation.

Tests individual components of mid-term goal generation, filtering, and prioritization.
"""

from models.state import GameState
from goals.manager import GoalManager
from goals.models import MidTermGoal


def test_get_mid_term_goals_returns_list():
    """get_mid_term_goals() should return a list, not a single goal."""
    gm = GoalManager()

    state = GameState(
        day=1,
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

    result = gm.get_mid_term_goals(state, {})

    assert isinstance(result, list)
    assert all(isinstance(g, MidTermGoal) for g in result)


def test_mid_term_goals_limited_to_max_three():
    """Should return at most 3 mid-term goals (avoid overwhelming LLM)."""
    gm = GoalManager()

    state = GameState(
        day=1,
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

    # Default limit is 3
    goals = gm.get_mid_term_goals(state, {})
    assert len(goals) <= 3


def test_mid_term_goals_limit_parameter():
    """Should respect optional limit parameter."""
    gm = GoalManager()

    state = GameState(
        day=1,
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

    # Request only 1 goal
    goals_one = gm.get_mid_term_goals(state, {}, limit=1)
    assert len(goals_one) == 1

    # Request 2 goals
    goals_two = gm.get_mid_term_goals(state, {}, limit=2)
    assert len(goals_two) <= 2

    # Request 5 goals (should be capped by available options)
    goals_five = gm.get_mid_term_goals(state, {}, limit=5)
    assert len(goals_five) <= 5


def test_mid_term_goals_have_required_fields():
    """All mid-term goals should have description, goal_check, and focus_actions."""
    gm = GoalManager()

    state = GameState(
        day=5,
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

    goals = gm.get_mid_term_goals(state, {})

    for goal in goals:
        assert hasattr(goal, "description")
        assert hasattr(goal, "goal_check")
        assert hasattr(goal, "focus_actions")
        assert goal.description != ""
        assert goal.goal_check is not None
        assert len(goal.focus_actions) > 0


def test_base_building_offered_when_no_science_machine():
    """Should offer 'Build base' goal when science machine not present."""
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
        nearby_entities=[],  # No science machine
    )

    goals = gm.get_mid_term_goals(state, {})

    # Should include base building goal
    has_base_goal = any(
        "base" in g.description.lower() or "science" in g.description.lower()
        for g in goals
    )
    assert has_base_goal


def test_base_building_not_offered_when_science_machine_exists():
    """Should NOT offer 'Build base' when science machine already exists."""
    gm = GoalManager()

    state = GameState(
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

    goals = gm.get_mid_term_goals(state, {})

    # Should NOT include base building (already have it)
    for goal in goals:
        # If it's a base building goal, it should be marked complete
        if "base" in goal.description.lower() or "science" in goal.description.lower():
            assert goal.goal_check(state) is True, (
                "Base building goal offered but science machine exists"
            )


def test_exploration_always_offered():
    """Exploration should always be a valid mid-term goal option."""
    gm = GoalManager()

    # Test in multiple contexts
    contexts = [
        # Early game
        GameState(
            day=1,
            time_of_day=0.5,
            phase="day",
            season="autumn",
            health=100,
            hunger=100,
            sanity=100,
            inventory=[],
            equipped=None,
            position={"x": 0, "z": 0},
        ),
        # Mid-game with science machine
        GameState(
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
            nearby_entities=[
                {"name": "science_machine", "type": "structure", "distance": 5}
            ],
        ),
    ]

    for state in contexts:
        goals = gm.get_mid_term_goals(state, {})

        # Should include exploration in some form
        has_explore = any(
            "explore" in g.description.lower() or "map" in g.description.lower()
            for g in goals
        )
        assert has_explore, (
            f"Exploration not offered for {state.season} day {state.day}"
        )


def test_food_stockpile_offered_when_low_food():
    """Should offer food stockpiling when food reserves are low."""
    gm = GoalManager()

    state = GameState(
        day=10,
        time_of_day=0.5,
        phase="day",
        season="winter",
        health=100,
        hunger=100,
        sanity=100,
        inventory=["log x5"],  # Has other items but low food
        equipped=None,
        position={"x": 0, "z": 0},
    )

    # Very low food in inventory
    goals = gm.get_mid_term_goals(state, {"log": 5})  # No food items

    # Should offer food stockpiling
    has_food_goal = any(
        "food" in g.description.lower() or "stockpile" in g.description.lower()
        for g in goals
    )
    assert has_food_goal


def test_seasonal_prep_offered_in_autumn():
    """Should offer winter preparation goals during autumn."""
    gm = GoalManager()

    state = GameState(
        day=5,
        time_of_day=0.5,
        phase="day",
        season="autumn",  # Winter approaching
        health=100,
        hunger=100,
        sanity=100,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
    )

    goals = gm.get_mid_term_goals(state, {})

    # Should offer winter prep or thermal stone crafting
    descriptions = [g.description.lower() for g in goals]
    has_winter_prep = any(
        "winter" in desc or "thermal" in desc or "warm" in desc for desc in descriptions
    )
    assert has_winter_prep


def test_mid_term_goal_predicates_are_callable():
    """All goal_check predicates should be callable with GameState."""
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

    goals = gm.get_mid_term_goals(state, {})

    for goal in goals:
        # Should be callable
        assert callable(goal.goal_check)

        # Should return boolean
        result = goal.goal_check(state)
        assert isinstance(result, bool)


def test_mid_term_goals_deduplicated():
    """Same goal should not appear multiple times in options."""
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

    goals = gm.get_mid_term_goals(state, {})

    # Check descriptions are unique
    descriptions = [g.description for g in goals]
    assert len(descriptions) == len(set(descriptions)), "Duplicate goals found"


def test_incomplete_goals_returned_first():
    """Incomplete goals should be prioritized over completed ones."""
    gm = GoalManager()

    # State with science machine (base goal complete)
    state = GameState(
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
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 5}
        ],
    )

    goals = gm.get_mid_term_goals(state, {})

    # All offered goals should be incomplete
    for goal in goals:
        assert goal.goal_check(state) is False, (
            f"Goal '{goal.description}' is complete but still offered"
        )


def test_mid_term_goals_context_changes_with_season():
    """Mid-term goal options should change based on season."""
    gm = GoalManager()

    autumn_state = GameState(
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

    winter_state = GameState(
        day=25,
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

    autumn_goals = gm.get_mid_term_goals(autumn_state, {})
    winter_goals = gm.get_mid_term_goals(winter_state, {})

    autumn_desc = [g.description.lower() for g in autumn_goals]
    winter_desc = [g.description.lower() for g in winter_goals]

    # Autumn should mention winter prep
    assert any("winter" in desc or "thermal" in desc for desc in autumn_desc)

    # Winter should NOT mention winter prep (already in winter)
    # Instead focus on survival strategies
    assert not any("prepare" in desc and "winter" in desc for desc in winter_desc)
