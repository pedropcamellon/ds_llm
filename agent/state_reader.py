"""
state_reader.py — Reads game_state.json and detects state changes / world resets.
"""

import hashlib
import json
from pathlib import Path


class StateReader:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._last_hash: str | None = None
        self._last_day: int = -1
        self._last_health: float = 100.0

    def read(self) -> dict | None:
        """Read and return the current game state, or None on failure."""
        if not self.state_file.exists():
            print(f"[StateReader] State file not found: {self.state_file}")
            return None
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[StateReader] Invalid JSON: {e}")
            return None
        except Exception as e:
            print(f"[StateReader] Read error: {e}")
            return None

    def has_changed(self, state: dict) -> bool:
        """Return True if state differs from the last seen snapshot."""
        h = hashlib.md5(json.dumps(state, sort_keys=True).encode()).hexdigest()
        if h != self._last_hash:
            self._last_hash = h
            return True
        return False

    def is_world_reset(self, state: dict) -> bool:
        """Return True if the day counter went back to 1 (new world)."""
        current_day = state.get("day", 0)
        reset = current_day == 1 and self._last_day > 1
        if reset:
            print("[StateReader] World reset detected!")
        self._last_day = current_day
        return reset

    def is_game_over(self, state: dict) -> bool:
        """Return True when Wilson's health just hit 0 (death transition)."""
        health = float(state.get("health", 100))
        dead = health <= 0 and self._last_health > 0
        if dead:
            print("[StateReader] Game over detected — Wilson died!")
        self._last_health = health
        return dead
