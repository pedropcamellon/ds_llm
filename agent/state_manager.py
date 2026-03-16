"""
state_manager.py — Centralized state file I/O, parsing, and validation helpers.

This module is the single place for:
- required-field extraction for safety-critical decisions
- game state file loading/parsing
- state-related errors
"""

from pathlib import Path
import json

from models import GameState


class StateFieldError(ValueError):
    """Raised when a required game-state field is missing or invalid."""


class StateFileError(ValueError):
    """Raised when game_state.json cannot be read or parsed safely."""


def require_field(state: GameState, key: str, cast: type = str):
    """Extract a required state field, raising StateFieldError if absent.

    Never use defaults for safety-critical fields - that can hide exporter bugs
    and cause the agent to make incorrect decisions.
    """
    value = getattr(state, key, None)
    if value is None:
        raise StateFieldError(
            f"[StateFieldError] Required field '{key}' is None in game_state - "
            "Lua exporter may be broken. PAUSE THE GAME and check log.txt."
        )
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise StateFieldError(
            f"[StateFieldError] Field '{key}' cannot be cast to {cast.__name__} "
            f"(got {value!r}). PAUSE THE GAME and check log.txt."
        ) from exc


def parse_game_state(data: dict) -> GameState:
    """Parse raw dict into validated GameState model."""
    try:
        return GameState.model_validate(data)
    except Exception as exc:
        raise StateFileError(f"Invalid game state payload: {exc}") from exc


def load_game_state_file(state_file: Path) -> GameState:
    """Load and parse game_state.json from disk."""
    if not state_file.exists():
        raise StateFileError(f"State file not found: {state_file}")

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise StateFileError(f"Invalid JSON in state file: {exc}") from exc
    except OSError as exc:
        raise StateFileError(f"Failed reading state file: {exc}") from exc

    return parse_game_state(data)
