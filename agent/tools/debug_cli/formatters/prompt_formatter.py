"""
prompt_formatter.py — Prompt-only output formatter.
"""

from .base import OutputFormatter


class PromptFormatter(OutputFormatter):
    """Formats only the LLM prompt."""

    def format(self, result, llm_response: dict | None = None) -> str:
        """Return just the prompt text."""
        return result.prompt_text
