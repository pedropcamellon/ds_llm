"""
utils/tests/test_parsing.py — Unit tests for generic parsing utilities.
"""

import pytest
from utils.parsing import parse_numbered_choice
from goals.models import MidTermGoal


@pytest.fixture
def sample_goals():
    """Create 3 sample mid-term goals for testing."""
    return [
        MidTermGoal(
            day_range="",
            description="Build base with science machine",
            focus_actions=["gather_resource", "craft_item"],
            reason="test_goal_1",
        ),
        MidTermGoal(
            day_range="",
            description="Stockpile food reserves",
            focus_actions=["gather_resource", "hunt_mob"],
            reason="test_goal_2",
        ),
        MidTermGoal(
            day_range="",
            description="Explore unmapped areas",
            focus_actions=["explore_map"],
            reason="test_goal_3",
        ),
    ]


class TestValidResponses:
    """Test parsing of valid LLM responses."""

    def test_parse_first_choice(self, sample_goals):
        """LLM responds with '1' → should return first goal."""
        result = parse_numbered_choice("1", sample_goals)
        assert result == sample_goals[0]
        assert result.description == "Build base with science machine"

    def test_parse_second_choice(self, sample_goals):
        """LLM responds with '2' → should return second goal."""
        result = parse_numbered_choice("2", sample_goals)
        assert result == sample_goals[1]
        assert result.description == "Stockpile food reserves"

    def test_parse_third_choice(self, sample_goals):
        """LLM responds with '3' → should return third goal."""
        result = parse_numbered_choice("3", sample_goals)
        assert result == sample_goals[2]
        assert result.description == "Explore unmapped areas"

    def test_parse_with_whitespace(self, sample_goals):
        """LLM responds with ' 2 ' → should strip and parse correctly."""
        result = parse_numbered_choice("  2  ", sample_goals)
        assert result == sample_goals[1]

    def test_parse_with_newlines(self, sample_goals):
        """LLM responds with '1\\n' → should strip and parse correctly."""
        result = parse_numbered_choice("1\n", sample_goals)
        assert result == sample_goals[0]


class TestMalformedResponses:
    """Test parsing of malformed LLM responses (extract digit if possible)."""

    def test_parse_full_description(self, sample_goals):
        """LLM responds with '1. Build base...' → should extract leading digit."""
        result = parse_numbered_choice("1. Build base with science machine", sample_goals)
        assert result == sample_goals[0]

    def test_parse_embedded_number(self, sample_goals):
        """LLM responds with 'I choose option 2' → should extract digit."""
        result = parse_numbered_choice("I choose option 2", sample_goals)
        assert result == sample_goals[1]

    def test_parse_number_words(self, sample_goals):
        """LLM responds with 'two' → should return None (can't parse words)."""
        result = parse_numbered_choice("two", sample_goals)
        assert result is None

    def test_parse_multiple_numbers_uses_first(self, sample_goals):
        """LLM responds with '2 or 3' → should use first number found."""
        result = parse_numbered_choice("2 or 3", sample_goals)
        assert result == sample_goals[1]  # Uses '2'


class TestInvalidResponses:
    """Test parsing of invalid LLM responses."""

    def test_parse_out_of_range_high(self, sample_goals):
        """LLM responds with '4' → should return None (out of range)."""
        result = parse_numbered_choice("4", sample_goals)
        assert result is None

    def test_parse_out_of_range_zero(self, sample_goals):
        """LLM responds with '0' → should return None (1-indexed)."""
        result = parse_numbered_choice("0", sample_goals)
        assert result is None

    def test_parse_negative_number(self, sample_goals):
        """LLM responds with '-1' → should return None."""
        result = parse_numbered_choice("-1", sample_goals)
        assert result is None

    def test_parse_empty_string(self, sample_goals):
        """LLM responds with '' → should return None."""
        result = parse_numbered_choice("", sample_goals)
        assert result is None

    def test_parse_no_number(self, sample_goals):
        """LLM responds with 'xyz' → should return None."""
        result = parse_numbered_choice("xyz", sample_goals)
        assert result is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_goals_list(self):
        """Empty goals list → should return None."""
        result = parse_numbered_choice("1", [])
        assert result is None

    def test_parse_single_goal(self):
        """Single goal, choice '1' → should work."""
        single_goal = [
            MidTermGoal(
                day_range="",
                description="Only option",
                focus_actions=[],
                reason="test",
            )
        ]
        result = parse_numbered_choice("1", single_goal)
        assert result == single_goal[0]

    def test_parse_two_goals_valid(self):
        """Two goals, choice '2' → should work."""
        two_goals = [
            MidTermGoal(day_range="", description="First", focus_actions=[], reason="test1"),
            MidTermGoal(day_range="", description="Second", focus_actions=[], reason="test2"),
        ]
        result = parse_numbered_choice("2", two_goals)
        assert result == two_goals[1]

    def test_parse_two_goals_invalid(self):
        """Two goals, choice '3' → should return None."""
        two_goals = [
            MidTermGoal(day_range="", description="First", focus_actions=[], reason="test1"),
            MidTermGoal(day_range="", description="Second", focus_actions=[], reason="test2"),
        ]
        result = parse_numbered_choice("3", two_goals)
        assert result is None
