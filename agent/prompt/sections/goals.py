"""
goals.py — Goals section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class GoalsSection(PromptSection):
    """Renders long-term and short-term goals."""

    def should_render(self, ctx: PromptContext) -> bool:
        return super().should_render(ctx) and bool(ctx.goals)

    def render(self, ctx: PromptContext) -> str:
        return (
            f"[GOALS]\n  {ctx.goals}\n[/GOALS]\n\n"
            f"Pick ONE mid-term goal by responding with the goal number and your full reasoning for choosing it. "
            f"Example response: '2 - Need to prepare for winter before it arrives'"
        )
