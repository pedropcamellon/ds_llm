"""Goal predicates — testable conditions for goal validation.

Predicates are Callable[[GameState], bool] functions that check whether
a goal condition is satisfied. They enable objective measurement of progress.

Each predicate is a factory function that returns a closure:
    predicate = health_above(50)  # Returns lambda
    predicate(state)               # Returns bool
"""

from typing import Callable
from models.state import GameState


# Type alias for readability
Predicate = Callable[[GameState], bool]


# ---------------------------------------------------------------------------
# Health predicates
# ---------------------------------------------------------------------------


def health_above(threshold: float) -> Predicate:
    """Returns predicate that checks if health >= threshold."""
    return lambda state: state.health >= threshold


def health_below(threshold: float) -> Predicate:
    """Returns predicate that checks if health < threshold."""
    return lambda state: state.health < threshold


# ---------------------------------------------------------------------------
# Hunger predicates
# ---------------------------------------------------------------------------


def hunger_above(threshold: float) -> Predicate:
    """Returns predicate that checks if hunger >= threshold."""
    return lambda state: state.hunger >= threshold


def hunger_below(threshold: float) -> Predicate:
    """Returns predicate that checks if hunger < threshold."""
    return lambda state: state.hunger < threshold


# ---------------------------------------------------------------------------
# Sanity predicates
# ---------------------------------------------------------------------------


def sanity_above(threshold: float) -> Predicate:
    """Returns predicate that checks if sanity >= threshold."""
    return lambda state: state.sanity >= threshold


def sanity_below(threshold: float) -> Predicate:
    """Returns predicate that checks if sanity < threshold."""
    return lambda state: state.sanity < threshold


# ---------------------------------------------------------------------------
# Inventory predicates
# ---------------------------------------------------------------------------


def has_item(item_name: str) -> Predicate:
    """Returns predicate that checks if item_name is in inventory.
    
    Works with dict inventory: {"log": 20, "torch": 1}
    Checks if item exists (count > 0).
    """
    def check(state: GameState) -> bool:
        return state.inventory.get(item_name, 0) > 0
    
    return check


def has_any_item(item_names: list[str]) -> Predicate:
    """Returns predicate that checks if ANY of the items are in inventory."""
    def check(state: GameState) -> bool:
        return any(state.inventory.get(name, 0) > 0 for name in item_names)
    
    return check


def has_item_count(item_name: str, min_count: int) -> Predicate:
    """Returns predicate that checks if item count >= min_count.
    
    Examples:
        has_item_count("twigs", 10)  # Need at least 10 twigs
        has_item_count("gold", 5)    # Need at least 5 gold
    """
    def check(state: GameState) -> bool:
        return state.inventory.get(item_name, 0) >= min_count
    
    return check


# ---------------------------------------------------------------------------
# Structure predicates (nearby_entities)
# ---------------------------------------------------------------------------


def has_structure(structure_name: str) -> Predicate:
    """Returns predicate that checks if structure is in nearby_entities.
    
    Expects nearby_entities as list of NearbyEntity objects with .name attribute.
    """
    def check(state: GameState) -> bool:
        if state.nearby_entities is None:
            return False
        return any(
            entity.name == structure_name
            for entity in state.nearby_entities
        )
    
    return check


# ---------------------------------------------------------------------------
# World predicates
# ---------------------------------------------------------------------------


def season_is(target_season: str) -> Predicate:
    """Returns predicate that checks if season matches (case-insensitive)."""
    def check(state: GameState) -> bool:
        return state.season.lower() == target_season.lower()
    
    return check


def day_between(min_day: int, max_day: int) -> Predicate:
    """Returns predicate that checks if day is in range [min_day, max_day] (inclusive)."""
    return lambda state: min_day <= state.day <= max_day


def phase_is(target_phase: str) -> Predicate:
    """Returns predicate that checks if phase matches (day/dusk/night)."""
    return lambda state: state.phase == target_phase


# ---------------------------------------------------------------------------
# Temperature predicates
# ---------------------------------------------------------------------------


def temperature_above(threshold: float) -> Predicate:
    """Returns predicate that checks if temperature >= threshold.
    
    Returns False if temperature is None (no data available).
    """
    def check(state: GameState) -> bool:
        if state.temperature is None:
            return False
        return state.temperature >= threshold
    
    return check


def temperature_below(threshold: float) -> Predicate:
    """Returns predicate that checks if temperature < threshold.
    
    Returns False if temperature is None (no data available).
    """
    def check(state: GameState) -> bool:
        if state.temperature is None:
            return False
        return state.temperature < threshold
    
    return check


# ---------------------------------------------------------------------------
# Composite helpers (for convenience)
# ---------------------------------------------------------------------------


def all_of(*predicates: Predicate) -> Predicate:
    """Returns predicate that checks if ALL predicates are satisfied (AND logic)."""
    return lambda state: all(pred(state) for pred in predicates)


def any_of(*predicates: Predicate) -> Predicate:
    """Returns predicate that checks if ANY predicate is satisfied (OR logic)."""
    return lambda state: any(pred(state) for pred in predicates)


def not_(predicate: Predicate) -> Predicate:
    """Returns predicate that negates the given predicate (NOT logic)."""
    return lambda state: not predicate(state)
