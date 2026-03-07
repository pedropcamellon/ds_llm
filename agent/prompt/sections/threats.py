"""
threats.py — Threats warning section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class ThreatsSection(PromptSection):
    """Renders active threats."""

    def should_render(self, ctx: PromptContext) -> bool:
        return super().should_render(ctx) and len(ctx.state.threats) > 0

    def render(self, ctx: PromptContext) -> str:
        state = ctx.state

        threat_lines = "\n".join(
            f"  [WARN] {t.name} at {t.distance}m [/WARN]" for t in state.threats
        )

        return f"""[THREATS]
{threat_lines}
[/THREATS]"""
