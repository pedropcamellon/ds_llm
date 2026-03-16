"""
strategic_prompt.py — Strategic planning prompt for LLM (phase-based).

This prompt is used when the phase changes (day→dusk→night→day).
LLM picks a high-level GOAL, not a micro-action.

Simpler, shorter prompt than the action-based one.
"""

from strategic_goals import (
    StrategicGoal,
    get_suggested_goals,
    format_goals_for_prompt,
)
from models import GameState


def build_strategic_prompt(
    state: GameState,
    inv: dict[str, int],
    phase_transition: str,
    memory_summary: str = "",
) -> str:
    """Build a strategic planning prompt for phase transitions.

    Args:
        state: Current game state
        inv: Current inventory dict
        phase_transition: e.g. "day → dusk" or "night → day"
        memory_summary: Brief summary of recent events

    Returns:
        Prompt string for LLM strategic decision
    """
    # Get suggested goals based on current situation
    threats_nearby = bool(state.threats)
    suggested = get_suggested_goals(
        phase=state.phase,
        health=state.health,
        hunger=state.hunger,
        inv=inv,
        threats_nearby=threats_nearby,
    )

    goals_text = format_goals_for_prompt(suggested)

    # Format inventory compactly
    inv_items = []
    for name, count in sorted(inv.items()):
        if count > 1:
            inv_items.append(f"{name} x{count}")
        else:
            inv_items.append(name)
    inv_line = ", ".join(inv_items) or "empty"

    # Build prompt
    return f"""You are Wilson in Don't Starve. It's now {phase_transition}.

[STATUS]
  Day {state.day} ({state.season}) | {state.phase}
  Health: {state.health:.0f} | Hunger: {state.hunger:.0f} | Sanity: {state.sanity:.0f}

[INVENTORY]
  {inv_line}

[RECENT]
  {memory_summary or "Nothing notable."}

[SUGGESTED GOALS]
{goals_text}

Pick ONE goal for this phase. Reply with JSON:
{{"goal":"goal_name","reason":"why this goal matters now"}}

Only pick from the suggested goals or say "explore_area" if none fit."""
