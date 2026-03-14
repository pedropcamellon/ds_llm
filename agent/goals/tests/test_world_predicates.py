"""Test world predicates — season, day, phase, temperature."""

import pytest
from models.state import GameState
from goals.predicates import (
    season_is,
    day_between,
    phase_is,
    temperature_above,
    temperature_below,
)


def test_season_is_when_matches():
    """season_is("winter") returns True when season == "winter"."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", season="winter")
    assert season_is("winter")(state) is True


def test_season_is_when_different():
    """season_is("winter") returns False when season == "autumn"."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", season="autumn")
    assert season_is("winter")(state) is False


def test_season_is_case_insensitive():
    """season_is("WINTER") matches "winter" (case-insensitive)."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", season="winter")
    assert season_is("WINTER")(state) is True


def test_day_between_when_in_range():
    """day_between(5, 10) returns True when day == 7."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", day=7)
    assert day_between(5, 10)(state) is True


def test_day_between_when_outside_range():
    """day_between(5, 10) returns False when day == 15."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", day=15)
    assert day_between(5, 10)(state) is False


def test_phase_is_when_matches():
    """phase_is("night") returns True when phase == "night"."""
    state = GameState(health=100, hunger=100, sanity=200, phase="night")
    assert phase_is("night")(state) is True


def test_temperature_above_when_warm():
    """temperature_above(20) returns True when temp >= 20."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", temperature=25)
    assert temperature_above(20)(state) is True


def test_temperature_below_when_freezing():
    """temperature_below(0) returns True when temp < 0."""
    state = GameState(health=100, hunger=100, sanity=200, phase="day", temperature=-5)
    assert temperature_below(0)(state) is True
