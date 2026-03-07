"""
actions_formatter.py — Actions-only output formatter.
"""

from collections import defaultdict

from .base import OutputFormatter


class ActionsFormatter(OutputFormatter):
    """Formats only the concrete actions list."""

    def format(self, result, llm_response: dict | None = None) -> str:
        """Format as grouped actions with targets arrays."""
        # Group actions by action name
        grouped_actions: dict[str, list[str | None]] = defaultdict(list)
        for opt in result.concrete_actions:
            grouped_actions[opt.action].append(opt.target)

        lines = ["[CONCRETE ACTIONS]"]
        for action_name, targets in grouped_actions.items():
            valid_targets = [t for t in targets if t is not None]
            if len(valid_targets) == 0:
                # Skip actions without targets
                continue
            else:
                targets_str = ", ".join(f'"{t}"' for t in valid_targets)
                lines.append(
                    f'  {{"action": "{action_name}", "targets": [{targets_str}]}}'
                )

        return "\n".join(lines)
