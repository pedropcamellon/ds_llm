"""
builder.py — Prompt builder orchestrating all sections.
"""

from models.state import GameState
from models.actions import ActionOption
from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class PromptBuilder:
    """Orchestrates prompt sections and builds final prompt string."""

    def __init__(self, sections: list[PromptSection]):
        self.sections = sections

    def build(
        self,
        state: GameState,
        valid_actions: list[ActionOption],
        goals: str = "",
        memory: list[dict] | None = None,
        last_action: str | None = None,
        last_action_changed: bool | None = None,
        world_history: str = "",
    ) -> str:
        """
        Build prompt by rendering all sections with shared context.

         Args:
             state: Current game state (Pydantic model)
             valid_actions: List of ActionOption instances
             goals: Formatted goals string from GoalManager
             memory: Recent memory entries from AgentMemory
             last_action: Action chosen on previous tick (for feedback)
             last_action_changed: Whether last action had an effect
             world_history: Recently-seen-but-gone entities summary

         Returns:
             Final prompt string with sections joined by double newlines
        """
        # Build typed context for all sections
        ctx = PromptContext(
            state=state,
            current_turn_actions=valid_actions,
            goals=goals,
            memory=memory or [],
            last_action=last_action,
            last_action_changed=last_action_changed,
            world_history=world_history,
        )

        # Render all sections and filter empty ones
        rendered = []
        for section in self.sections:
            text = section.format(ctx)
            if text:  # Skip empty sections
                rendered.append(text)

        # Join sections with double newlines
        return "\n\n".join(rendered)


def create_default_builder() -> PromptBuilder:
    """Factory function that creates PromptBuilder with default sections.

    Prompt structure optimized for two-phase decision making:
    Phase 1 (mid-term goal selection): Memory → Status → Inventory → Goals
    Phase 2 (action selection): Add ValidActionsSection when ready
    """
    from prompt.sections.instructions import InstructionsSection
    from prompt.sections.goals import GoalsSection

    # from prompt.sections.feedback import FeedbackSection
    from prompt.sections.status import StatusSection
    from prompt.sections.inventory import InventorySection
    from prompt.sections.memory import MemorySection
    # from prompt.sections.world_history import WorldHistorySection
    # from prompt.sections.last_action import LastActionSection
    # from prompt.sections.actions import ValidActionsSection  # TODO: Phase 2 - action selection

    sections = [
        InstructionsSection(),  # System prompt
        MemorySection(max_entries=6, lookahead=3),  # Recent context (moved up)
        StatusSection(),  # Current vitals
        InventorySection(),  # Resources available
        GoalsSection(),  # Long/mid/short-term goals (includes response format)
        # WorldHistorySection(),         # Optional: recently-seen entities
        # LastActionSection(),           # Optional: feedback from last action
        # ValidActionsSection(),         # Phase 2: Commented out for mid-term goal selection
    ]

    return PromptBuilder(sections)
