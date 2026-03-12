"""Unit tests for strategic_goals.py"""

import pytest
from models.state import GameState
from models.goals import StrategicGoal
from strategic_goals import (
    get_suggested_goals,
    is_goal_complete,
    get_goal_description,
)


def test_get_suggested_goals_day1():
    """Fresh game (day 1, morning) should suggest gather_basic_resources + explore_new_area."""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=[],  # Empty inventory
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {}  # No items

    goals = get_suggested_goals(state, inv)

    # Should suggest gathering basic resources and exploring
    goal_ids = [g.id for g in goals]
    assert "gather_basic_resources" in goal_ids
    assert "explore_new_area" in goal_ids

    # Should NOT suggest night prep (not dusk yet)
    assert "prepare_for_night" not in goal_ids

    # Goals should be ordered by priority (lower = more urgent)
    assert goals[0].priority <= goals[-1].priority


def test_get_suggested_goals_dusk():
    """Dusk without light source should prioritize prepare_for_night."""
    state = GameState(
        day=1,
        phase="dusk",
        time_of_day=0.85,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["cutgrass x3", "twigs x3"],
        equipped=None,  # No torch
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"cutgrass": 3, "twigs": 3}

    goals = get_suggested_goals(state, inv)

    # Should suggest night prep as top priority
    goal_ids = [g.id for g in goals]
    assert "prepare_for_night" in goal_ids

    # Prepare for night should be highest priority (priority=1)
    night_goal = next(g for g in goals if g.id == "prepare_for_night")
    assert night_goal.priority == 1


def test_get_suggested_goals_late_autumn():
    """Late autumn (day 12) with tools should suggest prepare_for_winter."""
    state = GameState(
        day=12,
        phase="day",
        time_of_day=0.5,
        season="autumn",
        health=150.0,
        hunger=120.0,
        sanity=180.0,
        inventory=["axe x1", "pickaxe x1", "log x5"],
        equipped="axe",
        position={"x": 10, "z": 20},
        nearby_entities=[],
        threats=[],
    )
    inv = {"axe": 1, "pickaxe": 1, "log": 5}

    goals = get_suggested_goals(state, inv)

    # Should suggest winter prep
    goal_ids = [g.id for g in goals]
    assert "prepare_for_winter" in goal_ids

    # Should NOT suggest gather_basic_resources (day > 3)
    assert "gather_basic_resources" not in goal_ids


def test_is_goal_complete_with_items():
    """Goal with all completion items present should return True."""
    state = GameState(
        day=2,
        phase="day",
        time_of_day=0.4,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["axe x1", "pickaxe x1", "cutgrass x5"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"axe": 1, "pickaxe": 1, "cutgrass": 5}

    # gather_basic_resources requires axe, pickaxe, cutgrass
    result = is_goal_complete("gather_basic_resources", state, inv)

    assert result is True


def test_is_goal_complete_missing_item():
    """Goal with missing completion items should return False."""
    state = GameState(
        day=2,
        phase="day",
        time_of_day=0.4,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["axe x1", "cutgrass x5"],  # Missing pickaxe
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"axe": 1, "cutgrass": 5}  # No pickaxe

    # gather_basic_resources requires axe, pickaxe, cutgrass
    result = is_goal_complete("gather_basic_resources", state, inv)

    assert result is False


def test_get_goal_description():
    """get_goal_description should return correct description string."""
    desc = get_goal_description("gather_basic_resources")

    assert "twigs" in desc.lower()
    assert "flint" in desc.lower()
    assert "grass" in desc.lower()


def test_is_goal_valid_filters_invalid():
    """Invalid goals should not appear in suggested list."""
    state = GameState(
        day=5,  # Too late for gather_basic_resources (only valid days 1-3)
        phase="day",
        time_of_day=0.4,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["axe x1", "pickaxe x1"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"axe": 1, "pickaxe": 1}

    goals = get_suggested_goals(state, inv)

    # Should NOT suggest gather_basic_resources (day > 3 and has tools)
    goal_ids = [g.id for g in goals]
    assert "gather_basic_resources" not in goal_ids

    # Should still suggest explore (always valid)
    assert "explore_new_area" in goal_ids
