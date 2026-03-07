"""
status.py — Player status section (vitals, day, weather).
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext

CRITICAL_VITALS_THRESHOLD = 50


def _stat_label(value, max_value) -> str:
    """Format a stat with critical warning."""
    try:
        v = float(value)
        status = "[CRITICAL]" if v < CRITICAL_VITALS_THRESHOLD else "[OK]"
        return f"{v:.0f}/{max_value} {status}"
    except (TypeError, ValueError):
        return f"{value}/{max_value}"


class StatusSection(PromptSection):
    """Renders player vitals, day, phase, season, weather."""

    def render(self, ctx: PromptContext) -> str:
        state = ctx.state

        # Weather
        rain_str = " RAINING" if state.is_raining else ""
        temp_str = (
            f" Temp:{state.temperature}C" if state.temperature is not None else ""
        )

        # Current action
        current_action_line = ""
        if state.current_action:
            current_action_line = (
                f"  Doing: {state.current_action}"
                + (f" -> {state.action_target}" if state.action_target else "")
                + "\n"
            )

        return f"""[STATUS]
  Day:{state.day} Phase:{state.phase} Season:{state.season}{rain_str}{temp_str}
  Health:{_stat_label(state.health, 100)} Hunger:{_stat_label(state.hunger, 150)} Sanity:{_stat_label(state.sanity, 200)}
  Equipped:{state.equipped or "none"}
{current_action_line}[/STATUS]"""
