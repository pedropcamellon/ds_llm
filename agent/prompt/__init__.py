"""
prompt/ — Modular prompt generation system.

The prompt builder uses the Builder pattern with composable sections.
Each section implements PromptSection and handles one aspect of the prompt.

Usage:
    from prompt import build_prompt

    prompt_text = build_prompt(
        state=game_state,
        valid_actions=actions_list,
        goals={"long_term": [...], "short_term": [...]}
    )
"""

from prompt.builder import PromptBuilder, create_default_builder
from models.state import GameState
from models.actions import ActionOption

# Module-level builder instance (created once, reused)
_default_builder: PromptBuilder | None = None


def build_prompt(
    state: GameState,
    memory: list[dict] | None = None,
    inv: dict[str, int] | None = None,
    *,
    last_action: str | None = None,
    last_action_changed: bool | None = None,
    world_history: str = "",
    valid_actions: list[ActionOption] | None = None,
    goals: str = "",
) -> str:
    """
    Build prompt string from game state and valid actions.

    This is the main entry point that maintains API compatibility
    with the old monolithic prompt.py while using the new modular system.

    Args:
        state: Game state Pydantic model
        memory: Recent memory entries from AgentMemory
        inv: DEPRECATED - inventory dict (unused, gets from state.get_inventory_dict())
        last_action: Action chosen on previous tick (for feedback)
        last_action_changed: Whether last action had an effect
        world_history: Recently-seen-but-gone entities summary
        valid_actions: List of ActionOption instances        goals: Formatted goals string from GoalManager

    Returns:
        Complete prompt string ready for LLM
    """
    global _default_builder

    # Lazy-create the default builder on first call
    if _default_builder is None:
        _default_builder = create_default_builder()

    # Use empty list if valid_actions not provided (backward compat)
    valid_actions = valid_actions or []

    return _default_builder.build(
        state, valid_actions, goals, memory, last_action, last_action_changed, world_history
    )


__all__ = [
    "build_prompt",
    "PromptBuilder",
    "create_default_builder",
]
