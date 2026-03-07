"""
base.py — Abstract base class for prompt sections.

Each section is responsible for rendering one part of the prompt.
"""

from abc import ABC, abstractmethod

from prompt.sections.context import PromptContext


class PromptSection(ABC):
    """Base class for prompt sections following Template Method pattern."""

    def __init__(self, enabled: bool = True):
        """Initialize section with optional enable/disable flag."""
        self.enabled = enabled

    @abstractmethod
    def render(self, ctx: PromptContext) -> str:
        """
        Render this section given the context.

        Args:
            ctx: Typed prompt context with state, actions, memory, etc.

        Returns:
            Rendered section string, or empty string if section should be skipped.
        """
        pass

    def should_render(self, ctx: PromptContext) -> bool:
        """Override to conditionally render based on context."""
        return self.enabled

    def format(self, ctx: PromptContext) -> str:
        """
        Public method to render section (Template Method).

        Checks should_render() before calling render().
        """
        if not self.should_render(ctx):
            return ""
        return self.render(ctx)
