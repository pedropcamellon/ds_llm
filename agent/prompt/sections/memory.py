"""
memory.py — Agent memory section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class MemorySection(PromptSection):
    """Renders recent memory with deduplication."""

    def __init__(self, max_entries: int = 8, lookahead: int = 12):
        super().__init__()
        self.max_entries = max_entries
        self.lookahead = lookahead

    def render(self, ctx: PromptContext) -> str:
        memory = ctx.memory

        if not memory:
            return "[MEMORY]\n  (none)\n[/MEMORY]"

        # Deduplicate consecutive llm_reason entries
        filtered: list[dict] = []
        last_llm_reason: str | None = None

        for entry in memory[-self.lookahead :]:
            if entry.get("source") == "llm_reason":
                if entry["text"] == last_llm_reason:
                    continue  # Skip duplicate
                last_llm_reason = entry["text"]
            filtered.append(entry)

        # Show most recent entries
        lines = []
        for entry in filtered[-self.max_entries :]:
            source = entry.get("source", "event")
            text = entry.get("text", "")
            lines.append(f"  - [{source}] {text}")

        return f"""[MEMORY]
{chr(10).join(lines)}
[/MEMORY]"""
