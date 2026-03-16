"""
json_formatter.py — JSON output formatter for GOAP-based agent.
"""

import json

from .base import OutputFormatter, format_state_summary


class JsonFormatter(OutputFormatter):
    """Formats agent decision result as JSON."""

    def format(self, result, llm_response: dict | None = None) -> str:
        """Format as machine-readable JSON."""
        output = {
            "mode": result.mode,
            "current_goal": result.current_goal,
            "llm_called": result.llm_called,
            "action": result.action,
            "state_summary": format_state_summary(result.state),
        }

        if result.prompt_text:
            output["prompt"] = result.prompt_text

        return json.dumps(output, indent=2)
