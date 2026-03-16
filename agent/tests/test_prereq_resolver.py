"""Unit tests for prereq_resolver.py"""

import pytest
from models.state import GameState, NearbyEntity
from models.actions import ActionCommand
from prereq_resolver import (
    resolve_next_action,
    get_prereq_chain,
    can_achieve_now,
    PrereqStep,
)


def test_resolve_axe_with_materials():
    """Has twigs+flint in inventory → should return craft:axe"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["twigs x3", "flint x2"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"twigs": 3, "flint": 2}

    action = resolve_next_action("gather_basic_resources", state, inv)

    assert action.action == "craft"
    assert action.target == "axe"
    assert "axe" in action.reason.lower()


def test_resolve_axe_missing_twigs():
    """Has flint, twigs on ground nearby → should return pick_up_item:twigs"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["flint x1"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            NearbyEntity(name="twigs", type="item", distance=5.2),
        ],
        threats=[],
    )
    inv = {"flint": 1}

    action = resolve_next_action("gather_basic_resources", state, inv)

    assert action.action == "pick_up_item"
    assert action.target == "twigs"


def test_resolve_axe_missing_flint():
    """Has twigs, flint on ground nearby → should return pick_up_item:flint"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["twigs x2"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            NearbyEntity(name="flint", type="item", distance=8.1),
        ],
        threats=[],
    )
    inv = {"twigs": 2}

    action = resolve_next_action("gather_basic_resources", state, inv)

    assert action.action == "pick_up_item"
    assert action.target == "flint"


def test_resolve_axe_nothing_nearby():
    """No materials in inventory or nearby → should return explore"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],  # Nothing nearby
        threats=[],
    )
    inv = {}

    action = resolve_next_action("gather_basic_resources", state, inv)

    assert action.action == "explore"
    # Should mention needing to find resources
    assert "gather_basic_resources" in action.reason or "axe" in action.reason.lower()


def test_resolve_chop_without_axe():
    """Tree nearby but no axe → should resolve axe prerequisites first"""
    state = GameState(
        day=2,
        phase="day",
        time_of_day=0.4,
        season="autumn",
        health=150.0,
        hunger=120.0,
        sanity=180.0,
        inventory=[],
        equipped=None,
        position={"x": 10, "z": 5},
        nearby_entities=[
            NearbyEntity(name="evergreen", type="plant", distance=7.3),
            NearbyEntity(name="twigs", type="item", distance=12.0),
            NearbyEntity(name="flint", type="item", distance=15.0),
        ],
        threats=[],
    )
    inv = {}

    # Goal that requires logs (which need chopping)
    action = resolve_next_action("prepare_for_winter", state, inv)

    # Should resolve axe dependency first (pick up twigs or flint)
    assert action.action in ["pick_up_item", "explore"]
    # If pick_up_item, should be gathering materials for axe
    if action.action == "pick_up_item":
        assert action.target in ["twigs", "flint"]


def test_can_achieve_now_pickup():
    """Item within range should return True for pick_up_item action"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=[],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            NearbyEntity(name="flint", type="item", distance=8.0),
        ],
        threats=[],
    )
    inv = {}

    action = {"action": "pick_up_item", "target": "flint"}

    result = can_achieve_now(action, state, inv)

    assert result is True


def test_can_achieve_now_tool_gated():
    """Chop action without axe should return False"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=[],  # No axe
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[
            NearbyEntity(name="evergreen", type="plant", distance=10.0),
        ],
        threats=[],
    )
    inv = {}

    action = {"action": "chop", "target": "evergreen"}

    result = can_achieve_now(action, state, inv)

    assert result is False  # Can't chop without axe


def test_get_prereq_chain_simple():
    """Prereq chain for axe should list craft→twigs, craft→flint"""
    inv = {}  # Empty inventory

    chain = get_prereq_chain("axe", inv)

    # Should contain axe as craft step
    axe_steps = [s for s in chain if s.item == "axe"]
    assert len(axe_steps) >= 1
    assert axe_steps[0].source == "craft"

    # Should contain prereqs for ingredients (twigs, flint)
    items_in_chain = [s.item for s in chain]
    # At minimum, axe itself should be in chain
    assert "axe" in items_in_chain


def test_can_achieve_now_craft_with_ingredients():
    """Craft action with all ingredients present should return True"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["twigs x2", "flint x1"],
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"twigs": 2, "flint": 1}

    action = {"action": "craft", "target": "axe"}

    result = can_achieve_now(action, state, inv)

    assert result is True


def test_can_achieve_now_craft_missing_ingredient():
    """Craft action missing an ingredient should return False"""
    state = GameState(
        day=1,
        phase="day",
        time_of_day=0.3,
        season="autumn",
        health=150.0,
        hunger=150.0,
        sanity=200.0,
        inventory=["twigs x2"],  # Has twigs but no flint
        equipped=None,
        position={"x": 0, "z": 0},
        nearby_entities=[],
        threats=[],
    )
    inv = {"twigs": 2}

    action = {"action": "craft", "target": "axe"}

    result = can_achieve_now(action, state, inv)

    assert result is False  # Missing flint
