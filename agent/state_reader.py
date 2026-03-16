"""
state_reader.py — Reads game_state.json and detects state changes / world resets.
"""

import hashlib
import json
from pathlib import Path

from models import GameState
from state_manager import StateFileError, load_game_state_file


class StateReader:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._last_hash: str | None = None
        self._last_day: int = -1
        self._last_health: float = 100.0
        self._last_phase: str = ""
        self._ticks_since_llm: int = 0

    def read(self) -> GameState | None:
        """Read and return the current game state, or None on failure."""
        try:
            return load_game_state_file(self.state_file)
        except StateFileError as e:
            print(f"[StateReader] {e}")

    def has_changed(self, state: GameState) -> bool:
        """Return True if state differs from the last seen snapshot."""
        # Convert Pydantic model to dict for JSON serialization
        state_dict = (
            state.model_dump() if hasattr(state, "model_dump") else state.dict()
        )
        h = hashlib.md5(json.dumps(state_dict, sort_keys=True).encode()).hexdigest()
        if h != self._last_hash:
            self._last_hash = h
            return True
        return False

    def is_world_reset(self, state: GameState) -> bool:
        """Return True if the day counter went back to 1 (new world)."""
        current_day = state.day
        reset = current_day == 1 and self._last_day > 1
        if reset:
            print("[StateReader] World reset detected!")
        self._last_day = current_day
        return reset

    def is_game_over(self, state: GameState) -> bool:
        """Return True when Wilson's health just hit 0 (death transition)."""
        health = float(state.health)
        dead = health <= 0 and self._last_health > 0
        if dead:
            print("[StateReader] Game over detected — Wilson died!")
        self._last_health = health
        return dead

    def phase_changed(self, state: GameState) -> bool:
        """Return True if time phase changed (day→dusk→night→day).

        DS phases: day, dusk, night. Transitions happen ~4x per game day.
        """
        current = state.phase.lower() if state.phase else "day"
        changed = current != self._last_phase and self._last_phase != ""
        if changed:
            print(f"[StateReader] Phase change: {self._last_phase} → {current}")
        self._last_phase = current
        return changed

    def should_call_llm(
        self, state: GameState, min_ticks: int = 3, force_on_phase: bool = True
    ) -> tuple[bool, str]:
        """Decide if LLM should be called this tick.

        Returns (should_call, reason).

        LLM is called when:
        - Phase changed (day→dusk→night→day) — strategic re-planning
        - Minimum ticks elapsed since last LLM call — avoid noise
        - Major event (health critical, new threat) — handled by emergency override

        Args:
            state: Current game state
            min_ticks: Minimum ticks between LLM calls (default 3 = ~15s)
            force_on_phase: Always call LLM on phase change
        """
        self._ticks_since_llm += 1

        # Phase change = strategic moment, always re-plan
        if force_on_phase and self.phase_changed(state):
            self._ticks_since_llm = 0
            return True, f"phase_change:{state.phase}"

        # Cooldown: don't call LLM too often
        if self._ticks_since_llm < min_ticks:
            return False, f"cooldown:{self._ticks_since_llm}/{min_ticks}"

        # Enough ticks passed, allow LLM call
        self._ticks_since_llm = 0
        return True, "tick_interval"

    def reset_llm_cooldown(self) -> None:
        """Reset the LLM cooldown counter (e.g., after emergency override)."""
        self._ticks_since_llm = 0
