"""
base.py — Abstract base class for output formatters.

Defines the interface all formatters must implement (Interface Segregation).
"""

from abc import ABC, abstractmethod

from models import GameState


class OutputFormatter(ABC):
    """Abstract formatter for pipeline results."""

    @abstractmethod
    def format(self, result, llm_response: dict | None = None) -> str:
        """
        Format pipeline result for output.

        Args:
            result: PipelineResult instance
            llm_response: Optional LLM response dict (if --with-llm was used)

        Returns:
            Formatted string ready for printing
        """
        pass


def format_state_summary(state: GameState) -> str:
    """Format a compact state summary (shared utility)."""
    inv_display = ", ".join(state.inventory[:10])
    if len(state.inventory) > 10:
        inv_display += f" ... (+{len(state.inventory) - 10} more)"

    return f"""Day {state.day}, {state.season}, {state.phase} (time: {state.time_of_day:.2f})
Health: {state.health} | Hunger: {state.hunger} | Sanity: {state.sanity}
Temperature: {state.temperature}°C | Raining: {state.is_raining}
Inventory: {inv_display}
Equipped: {state.equipped or "none"}
Nearby entities: {len(state.nearby_entities)} | Threats: {len(state.threats)}"""
