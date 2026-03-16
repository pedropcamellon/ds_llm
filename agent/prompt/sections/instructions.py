"""
instructions.py — System instructions section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class InstructionsSection(PromptSection):
    """Renders system rules and instructions."""

    def __init__(self, rules: str | None = None):
        super().__init__()
        self.rules = rules or self._default_rules()

    def _default_rules(self) -> str:
        return """Survive in the wild. Your task: Review the STATUS, INVENTORY, and recent MEMORY, then choose ONE mid-term goal to pursue.
The GOALS section lists 2-3 tactical options — pick the number (1, 2, or 3) that best fits the current situation.

Consider:
- What resources are available nearby?
- What structures exist or are missing?
- What season is it and what challenges are coming?
- What does recent memory suggest about priorities?"""

    def render(self, ctx: PromptContext) -> str:
        return self.rules
