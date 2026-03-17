"""Tests for goal_manager.py — GoalManager long/short-term goal logic."""

import pytest
from goal_manager import GoalManager, Urgency
from models.state import GameState


@pytest.fixture()
def gm() -> GoalManager:
    return GoalManager()


# ---------------------------------------------------------------------------
# Long-term goals
# ---------------------------------------------------------------------------


def test_long_term_spring(gm):
    ltg = gm.get_long_term_goal(_state(season="spring"))
    assert ltg.season == "spring"


def test_long_term_summer(gm):
    ltg = gm.get_long_term_goal(_state(season="summer"))
    assert ltg.season == "summer"


def test_long_term_unknown_season_raises_value_error(gm):
    with pytest.raises(ValueError):
        gm.get_long_term_goal(_state(season="monsoon"))


def test_long_term_case_insensitive(gm):
    ltg = gm.get_long_term_goal(_state(season="WINTER"))
    assert ltg.season == "winter"


# ---------------------------------------------------------------------------
# Short-term goals — priority ordering (CRITICAL > URGENT > MODERATE > LOW)
# ---------------------------------------------------------------------------


def _state(**kwargs) -> GameState:
    base = {
        "health": 100,
        "hunger": 100,
        "sanity": 200,
        "phase": "day",
        "temperature": 20,
        "threats": [],
        "nearby_entities": [],
    }
    base.update(kwargs)
    return GameState(**base)


# ── CRITICAL tier ──────────────────────────────────────────────────────


def test_health_below_20_returns_critical(gm):
    """health < 20 → CRITICAL urgency"""
    state = _state(health=15)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.CRITICAL
    assert (
        "eat_food" in stg.preferred_actions or "run_from_enemy" in stg.preferred_actions
    )


def test_threat_present_returns_critical(gm):
    """threats[0] exists → CRITICAL urgency"""
    state = _state(threats=[{"name": "spider", "distance": 5}])
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.CRITICAL
    assert "run_from_enemy" in stg.preferred_actions


def test_critical_overrides_all_other_urgencies(gm):
    """CRITICAL (health < 20) beats URGENT (night) + MODERATE (hunger)"""
    state = _state(health=15, hunger=30, phase="night")
    stg = gm.get_short_term_goal(state, {})
    assert stg.urgency == Urgency.CRITICAL
    assert "eat_food" in stg.preferred_actions  # health fix, not fire


def test_threat_overrides_multiple_urgencies(gm):
    """CRITICAL (threat) beats URGENT (starving) + night"""
    state = _state(threats=[{"name": "hound", "distance": 3}], hunger=20, phase="night")
    stg = gm.get_short_term_goal(state, {})
    assert stg.urgency == Urgency.CRITICAL
    assert "run_from_enemy" in stg.preferred_actions


def test_critical_health_overrides_all(gm):
    state = _state(health=15, hunger=10, phase="night")
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.CRITICAL
    assert "eat_food" in stg.preferred_actions


def test_threat_returns_critical(gm):
    state = _state(threats=[{"name": "spider", "distance": 5}])
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.CRITICAL
    assert "run_from_enemy" in stg.preferred_actions


def test_threat_overrides_low_hunger(gm):
    state = _state(threats=[{"name": "spider", "distance": 5}], hunger=10)
    stg = gm.get_short_term_goal(state, {})
    assert stg.urgency == Urgency.CRITICAL
    assert "run_from_enemy" in stg.preferred_actions


def test_night_no_fire_is_urgent(gm):
    state = _state(phase="night")
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT
    assert "craft_item:torch" in stg.preferred_actions


def test_dusk_no_fire_is_urgent(gm):
    state = _state(phase="dusk")
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT


# ── URGENT tier ────────────────────────────────────────────────────────


def test_night_without_fire_returns_urgent(gm):
    """phase=night, no fire nearby → URGENT urgency"""
    state = _state(phase="night")
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT
    assert (
        "craft_item:torch" in stg.preferred_actions
        or "craft_item:campfire" in stg.preferred_actions
    )


def test_dusk_without_fire_returns_urgent(gm):
    """phase=dusk, no fire nearby → URGENT urgency"""
    state = _state(phase="dusk")
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT


def test_freezing_temp_returns_urgent(gm):
    """temperature < 0 → URGENT urgency"""
    state = _state(temperature=-5)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT
    assert (
        "craft_item:campfire" in stg.preferred_actions
        or "craft_item:torch" in stg.preferred_actions
    )


def test_starving_returns_urgent(gm):
    """hunger < 25 → URGENT urgency"""
    state = _state(hunger=20)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT
    assert (
        "eat_food" in stg.preferred_actions
        or "gather_resource" in stg.preferred_actions
    )


# ── MODERATE tier ──────────────────────────────────────────────────────


def test_low_sanity_returns_moderate(gm):
    """sanity < 60 → MODERATE urgency"""
    state = _state(sanity=40)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.MODERATE


def test_moderate_hunger_returns_moderate(gm):
    """hunger < 50 (but >= 25) → MODERATE urgency"""
    state = _state(hunger=40)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.MODERATE


# ── STABLE / None ──────────────────────────────────────────────────────


def test_stable_state_returns_none(gm):
    """All stats good → None (no short-term goal)"""
    state = _state(health=100, hunger=100, sanity=200, phase="day", temperature=20)
    stg = gm.get_short_term_goal(state, {})
    assert stg is None


# ---------------------------------------------------------------------------
# Fire detection and inventory-based hints
# ---------------------------------------------------------------------------


def test_night_fire_nearby_lowers_urgency_to_low(gm):
    """phase=night + fire nearby → LOW urgency (safe to stay near fire)"""
    state = _state(
        phase="night",
        nearby_entities=[{"name": "campfire", "type": "structure", "distance": 5}],
    )
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.LOW


def test_night_with_torch_materials_suggests_craft(gm):
    """Night + inv has torch materials → description hints craft_item:torch"""
    state = _state(phase="night")
    inv = {"twigs": 2, "cutgrass": 2}
    stg = gm.get_short_term_goal(state, inv)
    assert "craft_item:torch" in stg.description


def test_night_with_campfire_materials_suggests_craft(gm):
    """Night + inv has campfire materials → description hints craft_item:campfire"""
    state = _state(phase="night")
    inv = {"log": 2, "cutgrass": 3}
    stg = gm.get_short_term_goal(state, inv)
    assert "craft_item:campfire" in stg.description


def test_night_without_materials_suggests_gathering(gm):
    """Night + no materials → description hints gathering twigs/grass"""
    state = _state(phase="night")
    inv = {"twigs": 0, "cutgrass": 0}
    stg = gm.get_short_term_goal(state, inv)
    assert "Gather" in stg.description or "gather" in stg.description


# ---------------------------------------------------------------------------
# format_for_prompt
# ---------------------------------------------------------------------------


def test_format_for_prompt_contains_season(gm):
    state = _state(season="winter")
    result = gm.format_for_prompt(state, {})
    assert "Winter" in result


def test_format_for_prompt_stable_has_no_urgency_label(gm):
    state = _state(season="autumn")
    result = gm.format_for_prompt(state, {})
    assert "Stable" in result


def test_format_for_prompt_urgent_includes_label(gm):
    state = _state(health=10, season="autumn")
    result = gm.format_for_prompt(state, {})
    assert "CRITICAL" in result
