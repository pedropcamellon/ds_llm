"""
last_action.py — Last action feedback section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class LastActionSection(PromptSection):
    """Renders feedback about the last action taken."""

    def should_render(self, ctx: PromptContext) -> bool:
        return super().should_render(ctx) and ctx.last_action is not None

    def render(self, ctx: PromptContext) -> str:
        last_action = ctx.last_action
        last_action_changed = ctx.last_action_changed

        if last_action_changed is False:
            feedback = f"  {last_action} -> no state change (action had no effect)"
        elif last_action_changed is True:
            feedback = f"  {last_action} -> state changed"
        else:
            return ""  # Unknown state change

        return f"""[LAST_ACTION]
{feedback}
[/LAST_ACTION]"""
