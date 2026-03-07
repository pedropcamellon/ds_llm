"""
base.py — Abstract base class for output formatters.

Defines the interface all formatters must implement (Interface Segregation).
"""

from abc import ABC, abstractmethod


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


def format_state_summary(state: dict) -> str:
    """Format a compact state summary (shared utility)."""
    inv_items = state.get("inventory", [])
    inv_display = ", ".join(inv_items[:10])
    if len(inv_items) > 10:
        inv_display += f" ... (+{len(inv_items) - 10} more)"

    return f"""Day {state.get("day", "?")}, {state.get("season", "?")}, {state.get("phase", "?")} (time: {state.get("time_of_day", 0):.2f})
Health: {state.get("health", "?")} | Hunger: {state.get("hunger", "?")} | Sanity: {state.get("sanity", "?")}
Temperature: {state.get("temperature", "?")}°C | Raining: {state.get("is_raining", False)}
Inventory: {inv_display}
Equipped: {state.get("equipped", "none")}
Nearby entities: {len(state.get("nearby_entities", []))} | Threats: {len(state.get("threats", []))}"""
