"""
actions.py — Valid actions section.
"""

from collections import defaultdict

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class ValidActionsSection(PromptSection):
    """Renders valid actions as a simple table format."""

    def __init__(self, instructions: str | None = None):
        super().__init__()
        self.instructions = instructions or self._default_instructions()

    def _default_instructions(self) -> str:
    return """Pick ONE action and ONE target from this action's list and reply with JSON using format: {"action":"action_name","target":"chosen_target","reason":"why"}"""

    def render(self, ctx: PromptContext) -> str:
        valid_actions = ctx.current_turn_actions

        if not valid_actions:
            actions_text = "  explore: N, S, E, W, NE, NW, SE, SW"
        else:
            # Group actions by action name
            grouped: dict[str, list[str | None]] = defaultdict(list)
            for opt in valid_actions:
                grouped[opt.action].append(opt.target)

            # Format as simple "action: target1, target2, ..." lines
            action_lines = []
            for action_name, targets in grouped.items():
                valid_targets = [t for t in targets if t is not None]
                if not valid_targets:
                    continue
                targets_str = ", ".join(valid_targets)
                action_lines.append(f"  {action_name}: {targets_str}")

            actions_text = "\n".join(action_lines)

        return f"""{self.instructions}
[ACTIONS]
{actions_text}
[/ACTIONS]"""
