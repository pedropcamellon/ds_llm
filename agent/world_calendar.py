"""
world_calendar.py — Don't Starve world calendar and temporal calculations.

Provides season cycle constants and functions for calculating:
- Next season in the cycle
- Current day within season (1-16)
- Days remaining until next season
- Human-readable season progress strings

This is game world domain knowledge, independent of goals or agent logic.

NOTE: Named 'world_calendar' to avoid conflict with Python's standard library 'calendar' module.

TODO: Current implementation assumes uniform 16-day seasons for simplicity.
      In actual Don't Starve vanilla, seasons have different lengths:
        - Autumn: 20 days
        - Winter: 16 days
        - Spring: 20 days
        - Summer: 16 days
      Functions should be updated to use actual per-season day counts.
"""

from enum import StrEnum


class Season(StrEnum):
    """Don't Starve season enumeration."""

    AUTUMN = "autumn"
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"


# Don't Starve seasons are 16 days each (vanilla single-player)
# TODO: This is a simplification - actual lengths vary by season (see module docstring)
SEASON_LENGTH = 16

# Actual season lengths in Don't Starve vanilla (for future use)
ACTUAL_SEASON_LENGTHS = {
    Season.AUTUMN: 20,
    Season.WINTER: 16,
    Season.SPRING: 20,
    Season.SUMMER: 16,
}

# Total days in a full year cycle
YEAR_LENGTH = sum(ACTUAL_SEASON_LENGTHS.values())  # 72 days

# Season progression cycle (autumn → winter → spring → summer → autumn)
SEASON_CYCLE = {
    Season.AUTUMN: Season.WINTER,
    Season.WINTER: Season.SPRING,
    Season.SPRING: Season.SUMMER,
    Season.SUMMER: Season.AUTUMN,
}


def get_next_season(current: str | Season) -> Season:
    """Return the season that follows the current season.

    Args:
        current: Current season name (case-insensitive string or Season enum)

    Returns:
        Next season (Season enum)

    Raises:
        KeyError: If current is not a valid season name
    """
    if isinstance(current, str):
        current = Season(current.lower())
    return SEASON_CYCLE[current]


def get_days_in_season(day: int, season_length: int = SEASON_LENGTH) -> int:
    """Calculate which day of the current season (1-based).

    Don't Starve days follow a cycle: 16 autumn, 16 winter, 16 spring, 16 summer.
    This function calculates where we are within the current season.

    WARNING: This implementation assumes uniform season lengths (16 days each).
    In actual Don't Starve vanilla, seasons vary:
      - Autumn: 20 days
      - Winter: 16 days
      - Spring: 20 days
      - Summer: 16 days
    This is a KNOWN LIMITATION. For production use, this function should accept
    the current season and use actual per-season day counts.

    Examples:
        Day 1   → 1  (first day of autumn)
        Day 10  → 10 (tenth day of autumn)
        Day 16  → 16 (last day of autumn)
        Day 17  → 1  (first day of winter)
        Day 65  → 1  (first day of new cycle)

    Args:
        day: Game day number (1-based)
        season_length: Days per season (default: 16, assumes uniform seasons)

    Returns:
        Day within current season (1-based, range: 1 to season_length)
    """
    # Formula explanation:
    # - (day - 1): Convert to 0-based indexing
    # - % (season_length * 4): Modulo full year (64 days) for cycling
    # - % season_length: Modulo season length to get day within season
    # - + 1: Convert back to 1-based indexing
    # NOTE: Assumes uniform season lengths - NOT accurate for real DS game
    return ((day - 1) % (season_length * 4)) % season_length + 1


def get_days_until_next_season(day: int, season_length: int = SEASON_LENGTH) -> int:
    """Calculate days remaining until the next season arrives.

    Examples:
        Day 1  → 16 (16 days until winter)
        Day 10 → 7  (7 days until winter)
        Day 16 → 1  (1 day until winter)
        Day 17 → 16 (16 days until spring)

    Args:
        day: Game day number (1-based)
        season_length: Days per season (default: 16)

    Returns:
        Days until next season begins (inclusive of current day)
    """
    days_in = get_days_in_season(day, season_length)
    return season_length - days_in + 1


def format_season_progress(day: int, season: str) -> str:
    """Return human-readable season progress string.

    Examples:
        (1, "autumn")  → "Day 1/16 of Autumn"
        (10, "winter") → "Day 10/16 of Winter"  (if day 10 of winter cycle)
        (16, "spring") → "Day 16/16 of Spring"

    Args:
        day: Game day number (1-based)
        season: Current season name (will be capitalized in output)

    Returns:
        Formatted string: "Day X/16 of Season"
    """
    days_in = get_days_in_season(day)
    return f"Day {days_in}/{SEASON_LENGTH} of {season.capitalize()}"
