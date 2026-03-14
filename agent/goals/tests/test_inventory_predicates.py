"""Test inventory predicates — has_item, has_any_item."""

from models.state import GameState
from goals.predicates import has_item, has_any_item


def test_has_item_when_item_present():
    """has_item("log") returns True when inventory contains 'log x10'."""
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=["log x10", "torch x1", "twigs x5"]
    )
    assert has_item("log")(state) is True


def test_has_item_when_item_missing():
    """has_item("goldnugget") returns False when not in inventory."""
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=["log x10", "torch x1"]
    )
    assert has_item("goldnugget")(state) is False


def test_has_item_when_inventory_empty():
    """has_item returns False when inventory is []."""
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=[]
    )
    assert has_item("log")(state) is False


def test_has_any_item_when_one_present():
    """has_any_item(["log", "twigs"]) returns True when either is present."""
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=["log x10"]
    )
    assert has_any_item(["log", "twigs", "goldnugget"])(state) is True


def test_has_any_item_when_none_present():
    """has_any_item returns False when no items match."""
    state = GameState(
        health=100, hunger=100, sanity=200, phase="day",
        inventory=["log x10", "torch x1"]
    )
    assert has_any_item(["goldnugget", "rocks"])(state) is False
