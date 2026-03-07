"""Tests for StateReader — file reading, change detection, death/reset detection."""

import json
import pytest
from pathlib import Path
from state_reader import StateReader

from models import GameState


@pytest.fixture
def state_file(tmp_path):
    return tmp_path / "game_state.json"


@pytest.fixture
def reader(state_file):
    return StateReader(state_file)


def _write(state_file: Path, state: GameState) -> None:
    state_file.write_text(json.dumps(state))


# ── read ──────────────────────────────────────────────────────────────────────


def test_read_returns_none_when_file_missing(reader):
    assert reader.read() is None


def test_read_returns_dict(reader, state_file):
    _write(state_file, GameState(day=1, health=100))
    result = reader.read()
    assert result == {"day": 1, "health": 100}


def test_read_returns_none_on_invalid_json(reader, state_file):
    state_file.write_text("not json {{{")
    assert reader.read() is None


# ── has_changed ───────────────────────────────────────────────────────────────


def test_first_read_always_changed(reader):
    state = GameState(day=1)
    assert reader.has_changed(state) is True


def test_same_state_not_changed(reader):
    state = GameState(day=1, health=100)
    reader.has_changed(state)  # first call — marks as seen
    assert reader.has_changed(state) is False


def test_different_state_changed(reader):
    reader.has_changed({"day": 1, "health": 100})
    assert reader.has_changed({"day": 1, "health": 80}) is True


def test_key_order_irrelevant(reader):
    reader.has_changed({"a": 1, "b": 2})
    assert reader.has_changed({"b": 2, "a": 1}) is False


# ── is_game_over ──────────────────────────────────────────────────────────────


def test_game_over_on_health_zero_transition(reader):
    reader.is_game_over({"health": 50})  # establish last_health = 50
    assert reader.is_game_over({"health": 0}) is True


def test_game_over_not_triggered_when_already_dead(reader):
    reader.is_game_over({"health": 50})
    reader.is_game_over({"health": 0})  # death fires
    assert reader.is_game_over({"health": 0}) is False  # already 0 → 0, no transition


def test_game_over_not_triggered_while_alive(reader):
    reader.is_game_over({"health": 100})
    assert reader.is_game_over({"health": 80}) is False


# ── is_world_reset ────────────────────────────────────────────────────────────


def test_world_reset_day_1_after_higher_day(reader):
    reader.is_world_reset({"day": 5})  # establish last_day = 5
    assert reader.is_world_reset({"day": 1}) is True


def test_world_reset_not_triggered_on_first_day(reader):
    # last_day starts at -1, so day==1 with last_day==-1 should NOT fire
    assert reader.is_world_reset({"day": 1}) is False


def test_world_reset_not_triggered_on_normal_progression(reader):
    reader.is_world_reset({"day": 3})
    assert reader.is_world_reset({"day": 4}) is False
