"""
world_history.py — Recently seen entities section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class WorldHistorySection(PromptSection):
    """Renders recently seen but now out-of-view entities."""

    def should_render(self, ctx: PromptContext) -> bool:
        return super().should_render(ctx) and bool(ctx.world_history)

    def render(self, ctx: PromptContext) -> str:
        history = ctx.world_history
        return f"""[WORLD_HISTORY]
  Recently seen (now out of view): {history}
[/WORLD_HISTORY]"""
