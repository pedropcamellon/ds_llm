"""
actions_formatter.py — Goals-only output formatter.
"""

from .base import OutputFormatter


class ActionsFormatter(OutputFormatter):
    """Formats only the suggested strategic goals (renamed for backwards compat)."""

    def format(self, result, llm_response: dict | None = None) -> str:
        """Format as list of suggested goals with priority."""
        lines = [f"[SUGGESTED GOALS] ({len(result.suggested_goals)} available)"]
        
        for goal in result.suggested_goals:
            lines.append(
                f"  {goal.name} (priority: {goal.priority}) - {goal.description}"
            )

        return "\n".join(lines)
