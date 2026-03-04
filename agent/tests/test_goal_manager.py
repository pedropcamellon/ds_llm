"""Tests for goal_manager.py — GoalManager long/short-term goal logic."""

import pytest
from goal_manager import GoalManager, Urgency


@pytest.fixture()
def gm() -> GoalManager:
    return GoalManager()


# ---------------------------------------------------------------------------
# Long-term goals
# ---------------------------------------------------------------------------


def test_long_term_autumn(gm):
    ltg = gm.get_long_term_goal({"season": "autumn"})
    assert ltg.season == "autumn"
    # TODO Avoid checking strings
    assert "firepit" in ltg.description.lower() or "gather" in ltg.description.lower()


def test_long_term_winter(gm):
    ltg = gm.get_long_term_goal({"season": "winter"})
    assert ltg.season == "winter"
    assert "warm" in ltg.description.lower() or "fire" in ltg.description.lower()


def test_long_term_spring(gm):
    ltg = gm.get_long_term_goal({"season": "spring"})
    assert ltg.season == "spring"


def test_long_term_summer(gm):
    ltg = gm.get_long_term_goal({"season": "summer"})
    assert ltg.season == "summer"


def test_long_term_unknown_season_defaults_to_autumn(gm):
    ltg = gm.get_long_term_goal({"season": "monsoon"})
    assert ltg.season == "autumn"


def test_long_term_case_insensitive(gm):
    ltg = gm.get_long_term_goal({"season": "WINTER"})
    assert ltg.season == "winter"


# ---------------------------------------------------------------------------
# Short-term goals — priority ordering
# ---------------------------------------------------------------------------


def _state(**kwargs):
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
    return base


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


def test_night_fire_nearby_is_low(gm):
    state = _state(
        phase="night",
        nearby_entities=[{"name": "campfire", "type": "structure", "distance": 5}],
    )
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.LOW


def test_night_can_craft_torch_shows_hint(gm):
    state = _state(phase="night")
    inv = {"twigs": 2, "cutgrass": 2}
    stg = gm.get_short_term_goal(state, inv)
    assert "craft_item:torch" in stg.description
    assert "ready" in stg.description


def test_night_can_craft_campfire_shows_hint(gm):
    state = _state(phase="night")
    inv = {"log": 2, "cutgrass": 3}
    stg = gm.get_short_term_goal(state, inv)
    assert "craft_item:campfire" in stg.description
    assert "ready" in stg.description


def test_night_cannot_craft_shows_gather_hint(gm):
    state = _state(phase="night")
    inv = {"twigs": 0, "cutgrass": 0}
    stg = gm.get_short_term_goal(state, inv)
    assert "Gather" in stg.description or "gather" in stg.description


def test_freezing_temperature_is_urgent(gm):
    state = _state(temperature=-5)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.URGENT
    assert (
        "craft_item:campfire" in stg.preferred_actions
        or "craft_item:torch" in stg.preferred_actions
    )


def test_low_sanity_is_moderate(gm):
    state = _state(sanity=40)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.MODERATE


def test_moderate_hunger_is_moderate(gm):
    state = _state(hunger=40)
    stg = gm.get_short_term_goal(state, {})
    assert stg is not None
    assert stg.urgency == Urgency.MODERATE


def test_stable_state_returns_none(gm):
    state = _state(health=100, hunger=100, sanity=200, phase="day", temperature=20)
    stg = gm.get_short_term_goal(state, {})
    assert stg is None


# ---------------------------------------------------------------------------
# format_for_prompt
# ---------------------------------------------------------------------------


def test_format_for_prompt_contains_season(gm):
    state = _state()
    state["season"] = "winter"
    result = gm.format_for_prompt(state, {})
    assert "Winter" in result


def test_format_for_prompt_stable_has_no_urgency_label(gm):
    state = _state()
    state["season"] = "autumn"
    result = gm.format_for_prompt(state, {})
    assert "Stable" in result


def test_format_for_prompt_urgent_includes_label(gm):
    state = _state(health=10)
    state["season"] = "autumn"
    result = gm.format_for_prompt(state, {})
    assert "CRITICAL" in result
