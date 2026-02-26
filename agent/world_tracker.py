"""
world_tracker.py — Rolling memory of entities seen in nearby_entities across ticks.

The game only exports entities within ~30 units. Anything that wanders out of
range disappears from the next snapshot. WorldTracker persists what was recently
visible so the agent can reason about resources it saw a few ticks ago.
"""

import time
from dataclasses import dataclass


@dataclass
class SeenEntity:
    name: str
    type: str
    last_seen: float  # epoch seconds
    times_seen: int = 1


def _fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s ago"
    return f"{int(seconds / 60)}m ago"


class WorldTracker:
    def __init__(self, ttl_seconds: float = 120.0, max_entries: int = 30):
        """
        Args:
            ttl_seconds:  How long to remember an entity after it leaves view.
            max_entries:  Maximum number of entities to keep in memory.
        """
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._seen: dict[str, SeenEntity] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self, state: dict) -> None:
        """Ingest the current nearby_entities list and expire stale entries."""
        now = time.time()
        for ent in state.get("nearby_entities", []):
            key = ent.get("name", "unknown")
            if key in self._seen:
                self._seen[key].last_seen = now
                self._seen[key].times_seen += 1
            else:
                self._seen[key] = SeenEntity(
                    name=key,
                    type=ent.get("type", "unknown"),
                    last_seen=now,
                )

        # Expire anything not seen within TTL
        cutoff = now - self.ttl
        self._seen = {k: v for k, v in self._seen.items() if v.last_seen >= cutoff}

    def not_currently_visible(self, state: dict) -> list[SeenEntity]:
        """Return entities seen before but absent from current nearby_entities.

        Sorted most-recently-seen first. Capped at max_entries.
        Excludes entities still in the current snapshot (already shown in [NEARBY]).
        """
        current_names = {e.get("name") for e in state.get("nearby_entities", [])}
        past = [e for e in self._seen.values() if e.name not in current_names]
        past.sort(key=lambda e: e.last_seen, reverse=True)
        return past[: self.max_entries]

    def summary_lines(self, state: dict, now: float | None = None) -> str:
        """Return a compact prompt-ready string of recently-seen-but-gone entities."""
        now = now or time.time()
        past = self.not_currently_visible(state)
        if not past:
            return ""
        parts = [f"{e.name} ({_fmt_age(now - e.last_seen)})" for e in past[:10]]
        return ", ".join(parts)

    def reset(self) -> None:
        """Clear all tracked entities (call on death / world reset)."""
        self._seen = {}
