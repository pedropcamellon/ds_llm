"""Tests for InventoryTracker — inventory parsing and delta logging."""

from unittest.mock import MagicMock
from inventory_tracker import InventoryTracker


def _make_tracker():
    memory = MagicMock()
    tracker = InventoryTracker(memory)
    return tracker, memory


def _state(items: list[str]) -> dict:
    return {"inventory": items}


# ── _parse ────────────────────────────────────────────────────────────────────


def test_parse_single_item():
    tracker, _ = _make_tracker()
    result = tracker._parse(_state(["axe"]))
    assert result == {"axe": 1}


def test_parse_stacked_item():
    tracker, _ = _make_tracker()
    result = tracker._parse(_state(["log x20"]))
    assert result == {"log": 20}


def test_parse_mixed_items():
    tracker, _ = _make_tracker()
    result = tracker._parse(_state(["axe", "log x20", "twigs x5"]))
    assert result == {"axe": 1, "log": 20, "twigs": 5}


def test_parse_empty_inventory():
    tracker, _ = _make_tracker()
    assert tracker._parse(_state([])) == {}


def test_parse_strips_whitespace():
    tracker, _ = _make_tracker()
    result = tracker._parse(_state([" flint "]))
    assert "flint" in result


# ── update / current ─────────────────────────────────────────────────────────


def test_current_empty_before_first_update():
    tracker, _ = _make_tracker()
    assert tracker.current == {}


def test_update_sets_current():
    tracker, _ = _make_tracker()
    tracker.update(_state(["axe", "log x5"]))
    assert tracker.current == {"axe": 1, "log": 5}


def test_update_returns_current_counts():
    tracker, _ = _make_tracker()
    result = tracker.update(_state(["flint x3"]))
    assert result == {"flint": 3}


# ── delta logging ─────────────────────────────────────────────────────────────


def test_gained_item_logged():
    tracker, memory = _make_tracker()
    tracker.update(_state(["log x2"]))  # tick 1 — no delta (no prev)
    tracker.update(_state(["log x5"]))  # tick 2 — gained 3
    calls = [str(c) for c in memory.add.call_args_list]
    assert any("Gained" in c and "log x3" in c for c in calls)


def test_lost_item_logged():
    tracker, memory = _make_tracker()
    tracker.update(_state(["log x5"]))
    tracker.update(_state(["log x2"]))
    calls = [str(c) for c in memory.add.call_args_list]
    assert any("Lost" in c and "log x3" in c for c in calls)


def test_new_item_logged_as_gained():
    tracker, memory = _make_tracker()
    tracker.update(_state([]))
    tracker.update(_state(["axe"]))
    calls = [str(c) for c in memory.add.call_args_list]
    assert any("Gained" in c and "axe" in c for c in calls)


def test_no_delta_no_log_on_first_tick():
    tracker, memory = _make_tracker()
    tracker.update(_state(["log x5"]))
    # memory.add should NOT have been called (no previous state to diff against)
    memory.add.assert_not_called()


# ── reset ─────────────────────────────────────────────────────────────────────


def test_reset_clears_current():
    tracker, _ = _make_tracker()
    tracker.update(_state(["axe"]))
    tracker.reset()
    assert tracker.current == {}
