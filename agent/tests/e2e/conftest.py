"""Shared fixtures and utilities for e2e tests."""

import json
import pytest
from pathlib import Path
from models.state import GameState


# Fixture directory relative to project root
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def load_fixture():
    """Factory fixture to load game state JSON files."""

    def _load(filename: str) -> GameState:
        """Load a fixture file and return validated GameState."""
        path = FIXTURES_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")

        with open(path) as f:
            data = json.load(f)

        return GameState(**data)

    return _load


@pytest.fixture
def day1_fresh(load_fixture):
    """Day 1 autumn start: empty inventory, basic resources nearby."""
    return load_fixture("day1_fresh.json")


@pytest.fixture
def day2_spring_inventory(load_fixture):
    """Day 2 spring: some items collected, tools available."""
    return load_fixture("day2_spring_inventory.json")


@pytest.fixture
def low_health_hostile(load_fixture):
    """Emergency: low health + hostile nearby."""
    return load_fixture("low_health_hostile.json")


@pytest.fixture
def night_no_fire(load_fixture):
    """Urgent: nighttime with no light source."""
    return load_fixture("night_no_fire.json")


@pytest.fixture
def winter_stocked(load_fixture):
    """Winter with stocked inventory: strategic planning needed."""
    return load_fixture("winter_stocked.json")
