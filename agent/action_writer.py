"""
action_writer.py — Writes the chosen action to action_command.json for the Lua mod.
"""

import json
from pathlib import Path

# Fields to hide from the one-line debug summary (written to file always)
_SKIP_IN_LOG = {"action", "reason"}


class ActionWriter:
    def __init__(self, action_file: Path):
        self.action_file = action_file

    def write(self, action: dict) -> None:
        """Persist action to disk so llm_action_executor.lua can pick it up."""
        try:
            with open(self.action_file, "w") as f:
                json.dump(action, f)

            # --- debug log ---
            reason_snippet = action.get("reason", "")[:120]
            extras = {k: v for k, v in action.items() if k not in _SKIP_IN_LOG}
            extra_str = (
                "  " + "  ".join(f"{k}={v}" for k, v in extras.items())
                if extras
                else ""
            )
            print(f"[ActionWriter] {action['action']}{extra_str}")
            print(f"             reason: {reason_snippet}")
        except Exception as e:
            print(f"[ActionWriter] Error writing action file: {e}")
