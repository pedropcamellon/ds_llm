"""
feedback.py — Wilson's speech and action results section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class FeedbackSection(PromptSection):
    """Renders speech log and action results."""

    def should_render(self, ctx: PromptContext) -> bool:
        state = ctx.state
        has_feedback = len(state.speech_log) > 0 or len(state.action_log) > 0
        return super().should_render(ctx) and has_feedback

    def render(self, ctx: PromptContext) -> str:
        state = ctx.state

        lines = []
        for s in state.speech_log:
            lines.append(f'  Wilson said: "{s}"')

        for a in state.action_log:
            if a.result == "failed":
                lines.append(f"  Action failed: {a.action} — {a.reason or '?'}")
            else:
                lines.append(f"  Action ok: {a.action}")

        return f"""[FEEDBACK]
{chr(10).join(lines)}
[/FEEDBACK]"""
