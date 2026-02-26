"""
inventory_tracker.py — Tracks inventory state and emits deltas between ticks.

Parse inventory strings, diff against previous tick,
and log changes to AgentMemory.
"""

from memory import AgentMemory


class InventoryTracker:
    def __init__(self, memory: AgentMemory):
        self.memory = memory
        self._prev: dict[str, int] = {}

    def reset(self) -> None:
        """Clear stored inventory (e.g. on world reset)."""
        self._prev = {}

    def update(self, state: dict) -> dict[str, int]:
        """Parse inventory from state, log any deltas, return current counts."""
        current = self._parse(state)
        if self._prev:
            self._log_delta(current)
        self._prev = current
        return current

    @property
    def current(self) -> dict[str, int]:
        return self._prev

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse(state: dict) -> dict[str, int]:
        """Convert ["log x20", "axe"] -> {"log": 20, "axe": 1}."""
        result: dict[str, int] = {}
        for item in state.get("inventory", []):
            if " x" in item:
                name, _, count = item.rpartition(" x")
                result[name.strip()] = int(count)
            else:
                result[item.strip()] = 1
        return result

    def _log_delta(self, current: dict[str, int]) -> None:
        gained, lost = [], []
        for key in set(current) | set(self._prev):
            prev = self._prev.get(key, 0)
            curr = current.get(key, 0)
            if curr > prev:
                gained.append(f"{key} x{curr - prev}")
            elif curr < prev:
                lost.append(f"{key} x{prev - curr}")
        if gained:
            self.memory.add(f"Gained: {', '.join(gained)}", "inventory")
        if lost:
            self.memory.add(f"Lost: {', '.join(lost)}", "inventory")
