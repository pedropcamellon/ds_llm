"""
state_loader.py — Loads and validates game state JSON files.

Single responsibility: file I/O for state snapshots.
"""

import json
from pathlib import Path


class StateLoadError(Exception):
    """Raised when state file cannot be loaded."""

    pass


class StateLoader:
    """Loads game state snapshots from JSON files."""

    @staticmethod
    def load(path: Path) -> dict:
        """
        Load game state from JSON file.

        Args:
            path: Path to game_state.json file

        Returns:
            Parsed game state dict

        Raises:
            StateLoadError: If file doesn't exist or parsing fails
        """
        if not path.exists():
            raise StateLoadError(f"State file not found: {path}")

        try:
            with open(path) as f:
                state = json.load(f)
                return state
        except json.JSONDecodeError as e:
            raise StateLoadError(f"Invalid JSON in {path}: {e}")
        except Exception as e:
            raise StateLoadError(f"Failed to load {path}: {e}")
