"""
text_formatter.py — Full text output formatter.
"""

import json
from collections import defaultdict

from .base import OutputFormatter, format_state_summary


class TextFormatter(OutputFormatter):
    """Formats complete pipeline results as human-readable text."""

    def __init__(self, max_actions: int = 20):
        """Initialize with optional action display limit."""
        self.max_actions = max_actions

    def format(self, result, llm_response: dict | None = None) -> str:
        """Format as full text output with all sections."""
        sections = []

        # State summary
        sections.append("=" * 80)
        sections.append("[STATE SUMMARY]")
        sections.append(format_state_summary(result.state))

        # Goals
        sections.append("\n" + "=" * 80)
        sections.append("[GOALS]")
        sections.append(result.goals_text)
        if result.short_term_goal:
            sections.append(
                f"\nShort-term goal: {result.short_term_goal.description} "
                f"(urgency: {result.short_term_goal.urgency.name})"
            )

        # Concrete actions
        sections.append("\n" + "=" * 80)
        sections.append(
            f"[CONCRETE ACTIONS] ({len(result.concrete_actions)} available)"
        )

        # Group actions by name
        grouped_actions: dict[str, list[str | None]] = defaultdict(list)
        for opt in result.concrete_actions:
            grouped_actions[opt.action].append(opt.target)

        displayed = 0
        for action_name, targets in grouped_actions.items():
            if displayed >= self.max_actions:
                break
            valid_targets = [t for t in targets if t is not None]
            if len(valid_targets) == 0:
                continue
            else:
                targets_str = ", ".join(f'"{t}"' for t in valid_targets)
                sections.append(
                    f'  {{"action": "{action_name}", "targets": [{targets_str}]}}'
                )
            displayed += 1

        if len(result.concrete_actions) > self.max_actions:
            sections.append(
                f"  ... and {len(result.concrete_actions) - self.max_actions} more"
            )

        # Full prompt
        sections.append("\n" + "=" * 80)
        sections.append("[FULL PROMPT]")
        sections.append(result.prompt_text)

        # LLM response (if provided)
        if llm_response:
            sections.append("\n" + "=" * 80)
            sections.append("[LLM RESPONSE]")
            sections.append(llm_response.get("raw", ""))
            sections.append("\n[PARSED ACTION]")
            sections.append(json.dumps(llm_response.get("action", {}), indent=2))

        return "\n".join(sections)
