"""Tests for WorldTracker — rolling entity memory with TTL."""

import time
from world_tracker import WorldTracker


def _state(entities: list[dict]) -> dict:
    return {"nearby_entities": entities}


def _ent(name: str, type_: str = "other") -> dict:
    return {"name": name, "type": type_, "distance": 5.0}


# ── update / basic tracking ───────────────────────────────────────────────────

def test_new_entity_added(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=60.0)
    tracker.update(_state([_ent("pine_tree")]))
    assert "pine_tree" in tracker._seen


def test_times_seen_increments(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=60.0)
    tracker.update(_state([_ent("rabbit")]))
    monkeypatch.setattr(time, "time", lambda: t + 5)
    tracker.update(_state([_ent("rabbit")]))
    assert tracker._seen["rabbit"].times_seen == 2


def test_expired_entity_removed(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=30.0)
    tracker.update(_state([_ent("spider")]))
    # Jump past TTL
    monkeypatch.setattr(time, "time", lambda: t + 60)
    tracker.update(_state([]))   # empty tick triggers expiry
    assert "spider" not in tracker._seen


def test_entity_within_ttl_kept(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=60.0)
    tracker.update(_state([_ent("rocks")]))
    monkeypatch.setattr(time, "time", lambda: t + 30)
    tracker.update(_state([]))
    assert "rocks" in tracker._seen


# ── not_currently_visible ─────────────────────────────────────────────────────

def test_not_visible_excludes_current(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=60.0)
    tracker.update(_state([_ent("tree"), _ent("rabbit")]))
    # Next tick only tree visible
    current_state = _state([_ent("tree")])
    past = tracker.not_currently_visible(current_state)
    names = [e.name for e in past]
    assert "rabbit" in names
    assert "tree" not in names


def test_not_visible_sorted_most_recent_first(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=120.0)
    tracker.update(_state([_ent("old_tree")]))
    monkeypatch.setattr(time, "time", lambda: t + 20)
    tracker.update(_state([_ent("new_rock")]))
    past = tracker.not_currently_visible(_state([]))
    assert past[0].name == "new_rock"
    assert past[1].name == "old_tree"


# ── summary_lines ─────────────────────────────────────────────────────────────

def test_summary_lines_empty_when_nothing_seen(monkeypatch):
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    tracker = WorldTracker()
    assert tracker.summary_lines(_state([])) == ""


def test_summary_lines_contains_entity_name(monkeypatch):
    t = 1000.0
    monkeypatch.setattr(time, "time", lambda: t)
    tracker = WorldTracker(ttl_seconds=60.0)
    tracker.update(_state([_ent("beefalo")]))
    monkeypatch.setattr(time, "time", lambda: t + 10)
    result = tracker.summary_lines(_state([]), now=t + 10)
    assert "beefalo" in result
    assert "10s ago" in result


# ── reset ─────────────────────────────────────────────────────────────────────

def test_reset_clears_all_entries(monkeypatch):
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    tracker = WorldTracker()
    tracker.update(_state([_ent("tree"), _ent("rock")]))
    tracker.reset()
    assert tracker._seen == {}
