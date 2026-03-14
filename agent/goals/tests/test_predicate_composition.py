"""Test predicate composition — AND/OR/NOT logic."""

from models.state import GameState
from goals.predicates import health_above, hunger_above, health_below


def test_predicates_compose_with_and():
    """Multiple predicates can be combined with 'and' logic."""
    state_healthy = GameState(health=80, hunger=70, sanity=150, phase="day")
    state_unhealthy = GameState(health=30, hunger=70, sanity=150, phase="day")

    # Both conditions must be true
    healthy_and_fed = lambda s: health_above(50)(s) and hunger_above(50)(s)

    assert healthy_and_fed(state_healthy) is True
    assert healthy_and_fed(state_unhealthy) is False


def test_predicates_compose_with_or():
    """Multiple predicates can be combined with 'or' logic."""
    state = GameState(health=30, hunger=70, sanity=150, phase="day")

    # Either condition can be true
    health_or_hunger_critical = lambda s: health_below(50)(s) or hunger_above(50)(s)

    assert health_or_hunger_critical(state) is True


def test_predicates_can_be_negated():
    """Predicates can be negated with 'not'."""
    state = GameState(health=80, hunger=100, sanity=200, phase="day")

    not_low_health = lambda s: not health_below(50)(s)

    assert not_low_health(state) is True
