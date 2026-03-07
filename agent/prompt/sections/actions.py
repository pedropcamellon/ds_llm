"""
actions.py — Valid actions section.
"""

from collections import defaultdict

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class ValidActionsSection(PromptSection):
    """Renders valid actions list with JSON format instructions."""

    def __init__(self, instructions: str | None = None):
        super().__init__()
        self.instructions = instructions or self._default_instructions()

    def _default_instructions(self) -> str:
        return """Reply ONLY with JSON — no extra text, no markdown, no explanation.
Each action shows "targets": [...]. Pick ONE value from the targets array.
Format: {"action":"action_name","target":"chosen_target","reason":"why"}"""

    def render(self, ctx: PromptContext) -> str:
        valid_actions = ctx.current_turn_actions

        if not valid_actions:
            actions_text = (
                '  {"action":"explore", "targets":["N","S","E","W","NE","NW","SE","SW"]}'
            )
        else:
            # Group actions by action name
            grouped: dict[str, list[str | None]] = defaultdict(list)
            for opt in valid_actions:
                grouped[opt.action].append(opt.target)

            # Format grouped actions - skip actions with no valid targets
            action_lines = []
            for action_name, targets in grouped.items():
                # Filter out None targets
                valid_targets = [t for t in targets if t is not None]
                if len(valid_targets) == 0:
                    continue  # Skip actions without targets
                
                # Always use "targets" array format for consistency
                targets_str = ", ".join(f'"{t}"' for t in valid_targets)
                action_lines.append(
                    f'  {{"action":"{action_name}", "targets":[{targets_str}]}}'
                )

            actions_text = "\n".join(action_lines)

        return f"""YOUR ONLY VALID CHOICES — pick exactly one action+target combination:
[VALID_ACTIONS]
{actions_text}
[/VALID_ACTIONS]

{self.instructions}"""
