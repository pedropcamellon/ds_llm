"""
action_writer.py — Writes the chosen action to action_command.json for the Lua mod.
"""

import json
from pathlib import Path


class ActionWriter:
    def __init__(self, action_file: Path):
        self.action_file = action_file

    def write(self, action: dict) -> None:
        """Persist action to disk so llm_action_executor.lua can pick it up."""
        try:
            with open(self.action_file, "w") as f:
                json.dump(action, f)
            print(f"[ActionWriter] action={action['action']}")
            print(f"[ActionWriter] reason={action['reason'][:120]}")
        except Exception as e:
            print(f"[ActionWriter] Error writing action file: {e}")
