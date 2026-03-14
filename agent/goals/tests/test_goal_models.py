"""Test goal models with predicates — goal_check field and completion validation.

Tests that goal models can have optional predicate fields for validation,
and that goals can be checked for completion.
"""

import pytest
from models.state import GameState
from goals.models import ShortTermGoal, MidTermGoal, LongTermGoal, Urgency
from goals.predicates import health_above, season_is, has_item, has_structure


# ---------------------------------------------------------------------------
# ShortTermGoal with goal_check
# ---------------------------------------------------------------------------


def test_short_term_goal_accepts_goal_check_predicate():
    """ShortTermGoal should accept optional goal_check predicate."""
    goal = ShortTermGoal(
        urgency=Urgency.CRITICAL,
        description="Restore health to 50+",
        preferred_actions=["eat_food"],
        goal_check=health_above(50),
        reason="health_critical"
    )
    
    assert goal.goal_check is not None
    assert callable(goal.goal_check)


def test_short_term_goal_check_returns_true_when_satisfied():
    """goal.goal_check(state) should return True when goal is achieved."""
    goal = ShortTermGoal(
        urgency=Urgency.CRITICAL,
        description="Restore health to 50+",
        preferred_actions=["eat_food"],
        goal_check=health_above(50),
        reason="health_critical"
    )
    
    state_healthy = GameState(health=75, hunger=100, sanity=200, phase="day")
    
    assert goal.goal_check(state_healthy) is True


def test_short_term_goal_check_returns_false_when_incomplete():
    """goal.goal_check(state) should return False when goal not achieved."""
    goal = ShortTermGoal(
        urgency=Urgency.CRITICAL,
        description="Restore health to 50+",
        preferred_actions=["eat_food"],
        goal_check=health_above(50),
        reason="health_critical"
    )
    
    state_injured = GameState(health=25, hunger=100, sanity=200, phase="day")
    
    assert goal.goal_check(state_injured) is False


def test_short_term_goal_without_goal_check_is_valid():
    """ShortTermGoal should work without goal_check (backward compat)."""
    goal = ShortTermGoal(
        urgency=Urgency.URGENT,
        description="Get warm",
        preferred_actions=["craft_item:campfire"],
        reason="freezing"
    )
    
    assert goal.goal_check is None


# ---------------------------------------------------------------------------
# MidTermGoal with goal_check
# ---------------------------------------------------------------------------


def test_mid_term_goal_accepts_goal_check_predicate():
    """MidTermGoal should accept optional goal_check predicate."""
    goal = MidTermGoal(
        day_range="Day 1-5",
        description="Build science machine",
        focus_actions=["gather_resource", "craft_item"],
        goal_check=has_structure("science_machine"),
        reason="base_building"
    )
    
    assert goal.goal_check is not None
    assert callable(goal.goal_check)


def test_mid_term_goal_check_validates_completion():
    """MidTermGoal.goal_check should validate when structure is built."""
    goal = MidTermGoal(
        day_range="Day 1-5",
        description="Build science machine",
        focus_actions=["gather_resource", "craft_item"],
        goal_check=has_structure("science_machine"),
        reason="base_building"
    )
    
    state_without_machine = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        season="autumn", day=3,
        nearby_entities=[]
    )
    
    state_with_machine = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        season="autumn", day=5,
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 2}
        ]
    )
    
    assert goal.goal_check(state_without_machine) is False
    assert goal.goal_check(state_with_machine) is True


# ---------------------------------------------------------------------------
# LongTermGoal with goal_check
# ---------------------------------------------------------------------------


def test_long_term_goal_accepts_goal_check_predicate():
    """LongTermGoal should accept optional goal_check predicate."""
    goal = LongTermGoal(
        season="winter",
        description="Survive winter — reach spring alive",
        focus_actions=["gather_resource", "stay_warm"],
        goal_check=season_is("spring")
    )
    
    assert goal.goal_check is not None
    assert callable(goal.goal_check)


def test_long_term_goal_check_validates_season_transition():
    """LongTermGoal.goal_check should validate when season changes."""
    goal = LongTermGoal(
        season="winter",
        description="Survive winter — reach spring alive",
        focus_actions=["gather_resource", "stay_warm"],
        goal_check=season_is("spring")
    )
    
    state_winter = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        season="winter", day=35
    )
    
    state_spring = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        season="spring", day=37
    )
    
    assert goal.goal_check(state_winter) is False
    assert goal.goal_check(state_spring) is True


# ---------------------------------------------------------------------------
# Filtering incomplete goals
# ---------------------------------------------------------------------------


def test_filter_incomplete_short_term_goals():
    """Can filter short-term goals to only incomplete ones."""
    goals = [
        ShortTermGoal(
            urgency=Urgency.URGENT,
            description="Gather 4 gold",
            preferred_actions=["gather_resource"],
            goal_check=has_item("goldnugget"),
            reason="need_gold"
        ),
        ShortTermGoal(
            urgency=Urgency.MODERATE,
            description="Gather wood",
            preferred_actions=["gather_resource"],
            goal_check=has_item("log"),
            reason="need_wood"
        ),
    ]
    
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=["log x10"]  # Has wood, no gold
    )
    
    incomplete = [g for g in goals if g.goal_check and not g.goal_check(state)]
    
    assert len(incomplete) == 1
    assert incomplete[0].description == "Gather 4 gold"


def test_filter_handles_goals_without_predicates():
    """Filtering should skip goals without goal_check (None)."""
    goals = [
        ShortTermGoal(
            urgency=Urgency.URGENT,
            description="Gather gold",
            preferred_actions=["gather_resource"],
            goal_check=has_item("goldnugget"),
            reason="need_gold"
        ),
        ShortTermGoal(
            urgency=Urgency.MODERATE,
            description="Stay warm",  # No predicate
            preferred_actions=["craft_item:campfire"],
            reason="freezing"
        ),
    ]
    
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=[]
    )
    
    # Only filter goals that have predicates
    incomplete = [g for g in goals if g.goal_check and not g.goal_check(state)]
    
    assert len(incomplete) == 1
    assert incomplete[0].description == "Gather gold"
