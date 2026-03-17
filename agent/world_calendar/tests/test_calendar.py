"""
tests/test_calendar.py — Unit tests for Don't Starve calendar/temporal utilities.

Tests season cycles, day calculations, and temporal formatting.
"""

import pytest
from world_calendar import (
    Season,
    SEASON_LENGTH,
    SEASON_CYCLE,
    get_next_season,
    get_days_in_season,
    get_days_until_next_season,
    format_season_progress,
)


class TestSeasonCycle:
    """Test season cycle constants and next season calculation."""

    def test_season_enum_values(self):
        """Season enum should contain all four seasons with correct values."""
        assert Season.AUTUMN.value == "autumn"
        assert Season.WINTER.value == "winter"
        assert Season.SPRING.value == "spring"
        assert Season.SUMMER.value == "summer"

    def test_season_length_constant(self):
        """Season length should be 16 days."""
        assert SEASON_LENGTH == 16

    def test_season_cycle_complete(self):
        """Season cycle should contain all four seasons (as enums)."""
        assert set(SEASON_CYCLE.keys()) == {Season.AUTUMN, Season.WINTER, Season.SPRING, Season.SUMMER}
        assert set(SEASON_CYCLE.values()) == {Season.AUTUMN, Season.WINTER, Season.SPRING, Season.SUMMER}

    def test_get_next_season_autumn(self):
        """Autumn should transition to winter."""
        assert get_next_season(Season.AUTUMN) == Season.WINTER
        assert get_next_season("autumn") == Season.WINTER

    def test_get_next_season_winter(self):
        """Winter should transition to spring."""
        assert get_next_season(Season.WINTER) == Season.SPRING
        assert get_next_season("winter") == Season.SPRING

    def test_get_next_season_spring(self):
        """Spring should transition to summer."""
        assert get_next_season(Season.SPRING) == Season.SUMMER
        assert get_next_season("spring") == Season.SUMMER

    def test_get_next_season_summer(self):
        """Summer should transition to autumn (cycle completes)."""
        assert get_next_season(Season.SUMMER) == Season.AUTUMN
        assert get_next_season("summer") == Season.AUTUMN

    def test_get_next_season_case_insensitive(self):
        """get_next_season should handle uppercase/mixed case strings."""
        assert get_next_season("AUTUMN") == Season.WINTER
        assert get_next_season("WinTer") == Season.SPRING


class TestDaysInSeason:
    """Test calculation of current day within season (1-16)."""

    def test_day_1_is_day_1_of_season(self):
        """Day 1 of the game should be day 1 of autumn."""
        assert get_days_in_season(1) == 1

    def test_day_16_is_last_day_of_first_season(self):
        """Day 16 should be the last day of autumn."""
        assert get_days_in_season(16) == 16

    def test_day_17_is_first_day_of_winter(self):
        """Day 17 should be day 1 of winter."""
        assert get_days_in_season(17) == 1

    def test_day_32_is_last_day_of_winter(self):
        """Day 32 should be day 16 of winter."""
        assert get_days_in_season(32) == 16

    def test_mid_season_day(self):
        """Day 10 of first season should return 10."""
        assert get_days_in_season(10) == 10

    def test_full_year_cycle(self):
        """Day 64 should wrap to day 16 of summer (end of year)."""
        # 16*4 = 64 days = full cycle
        assert get_days_in_season(64) == 16

    def test_day_65_starts_new_cycle(self):
        """Day 65 should be day 1 of new autumn cycle."""
        assert get_days_in_season(65) == 1

    def test_custom_season_length(self):
        """Should support custom season lengths for testing."""
        # If seasons were 10 days long:
        assert get_days_in_season(1, season_length=10) == 1
        assert get_days_in_season(10, season_length=10) == 10
        assert get_days_in_season(11, season_length=10) == 1


class TestDaysUntilNextSeason:
    """Test calculation of days remaining until next season."""

    def test_day_1_has_16_days_until_winter(self):
        """Day 1 of autumn should have 16 days until winter."""
        assert get_days_until_next_season(1) == 16

    def test_day_16_has_1_day_until_winter(self):
        """Day 16 of autumn (last day) should have 1 day until winter."""
        assert get_days_until_next_season(16) == 1

    def test_day_17_has_16_days_until_spring(self):
        """Day 17 (first day of winter) should have 16 days until spring."""
        assert get_days_until_next_season(17) == 16

    def test_mid_season(self):
        """Day 10 of autumn should have 7 days until winter."""
        assert get_days_until_next_season(10) == 7

    def test_custom_season_length(self):
        """Should support custom season lengths."""
        # Day 1 with 10-day seasons: 10 days until next
        assert get_days_until_next_season(1, season_length=10) == 10
        # Day 5 with 10-day seasons: 6 days until next
        assert get_days_until_next_season(5, season_length=10) == 6


class TestFormatSeasonProgress:
    """Test human-readable season progress formatting."""

    def test_format_day_1_autumn(self):
        """Day 1 should format as 'Day 1/16 of Autumn'."""
        result = format_season_progress(1, "autumn")
        assert "Day 1/16" in result
        assert "Autumn" in result

    def test_format_day_10_winter(self):
        """Day 26 (day 10 of winter) should show correct formatting."""
        # Day 26 = day 10 of winter (16 autumn + 10 winter)
        result = format_season_progress(26, "winter")
        assert "Day 10/16" in result
        assert "Winter" in result

    def test_format_last_day_of_season(self):
        """Day 16 should format as 'Day 16/16 of Autumn'."""
        result = format_season_progress(16, "autumn")
        assert "Day 16/16" in result
        assert "Autumn" in result

    def test_format_capitalizes_season(self):
        """Season name should be capitalized in output."""
        result = format_season_progress(1, "spring")
        assert "Spring" in result
        # Input lowercase should still produce capitalized output
        result_lower = format_season_progress(1, "spring")
        assert "Spring" in result_lower

    def test_format_handles_mid_cycle(self):
        """Day 50 (day 2 of summer) should format correctly."""
        # 16 autumn + 16 winter + 16 spring + 2 summer = 50
        result = format_season_progress(50, "summer")
        assert "Day 2/16" in result
        assert "Summer" in result
