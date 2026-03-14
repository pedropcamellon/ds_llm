"""Test stat predicates — health, hunger, sanity thresholds."""

import pytest
from models.state import GameState
from goals.predicates import (
    health_above,
    health_below,
    hunger_above,
    hunger_below,
    sanity_above,
    sanity_below,
)


def test_health_above_when_healthy():
    """health_above(50) returns True when health >= 50."""
    state = GameState(health=75, hunger=100, sanity=200, phase="day")
    assert health_above(50)(state) is True


def test_health_above_when_injured():
    """health_above(50) returns False when health < 50."""
    state = GameState(health=25, hunger=100, sanity=200, phase="day")
    assert health_above(50)(state) is False


def test_health_below_when_critical():
    """health_below(20) returns True when health < 20."""
    state = GameState(health=15, hunger=100, sanity=200, phase="day")
    assert health_below(20)(state) is True


def test_hunger_above_when_fed():
    """hunger_above(50) returns True when hunger >= 50."""
    state = GameState(health=100, hunger=75, sanity=200, phase="day")
    assert hunger_above(50)(state) is True


def test_hunger_below_when_starving():
    """hunger_below(25) returns True when hunger < 25."""
    state = GameState(health=100, hunger=20, sanity=200, phase="day")
    assert hunger_below(25)(state) is True


def test_sanity_above_when_sane():
    """sanity_above(100) returns True when sanity >= 100."""
    state = GameState(health=100, hunger=100, sanity=150, phase="day")
    assert sanity_above(100)(state) is True


def test_sanity_below_when_insane():
    """sanity_below(60) returns True when sanity < 60."""
    state = GameState(health=100, hunger=100, sanity=40, phase="day")
    assert sanity_below(60)(state) is True
