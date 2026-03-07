"""
nearby.py — Nearby entities section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class NearbySection(PromptSection):
    """Renders nearby entities list."""

    def __init__(self, max_entities: int = 5):
        super().__init__()
        self.max_entities = max_entities

    def render(self, ctx: PromptContext) -> str:
        state = ctx.state

        nearby_lines = (
            "\n".join(
                f"  - {e.name} ({e.type}) - {e.distance}m"
                for e in state.nearby_entities[: self.max_entities]
            )
            or "  (none)"
        )

        return f"""[NEARBY]
{nearby_lines}
[/NEARBY]"""
