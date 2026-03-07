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
        return """Survive in the wild. Survive as long as possible.
Always act on the SHORT-TERM GOAL first. If no urgent goal, work toward the LONG-TERM GOAL.
YOU MUST pick from VALID_ACTIONS (listed at the bottom). Never invent an action.
Use the exact action name and target from the list.
If your goal requires something not currently available (e.g. flint not nearby), pick explore — do NOT idle."""

    def render(self, ctx: PromptContext) -> str:
        return self.rules
