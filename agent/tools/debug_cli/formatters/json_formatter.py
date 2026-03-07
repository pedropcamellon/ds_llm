"""
json_formatter.py — JSON output formatter.
"""

import json

from .base import OutputFormatter, format_state_summary


class JsonFormatter(OutputFormatter):
    """Formats pipeline results as JSON."""

    def format(self, result, llm_response: dict | None = None) -> str:
        """Format as machine-readable JSON."""
        actions_display = [
            {"action": opt.action, "target": opt.target, "reason": opt.reason}
            for opt in result.concrete_actions
        ]

        output = {
            "state_summary": format_state_summary(result.state),
            "goals": result.goals_text,
            "short_term_goal": (
                result.short_term_goal.description if result.short_term_goal else None
            ),
            "concrete_actions": actions_display,
            "prompt": result.prompt_text,
        }

        if llm_response:
            output["llm_response"] = llm_response

        return json.dumps(output, indent=2)
