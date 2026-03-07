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
        return f"[GOALS]\n  {ctx.goals}\n[/GOALS]\n"
