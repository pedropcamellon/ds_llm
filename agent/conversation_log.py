"""
conversation_log.py — Appends full LLM prompt/response pairs to a JSONL file.

Separate from AgentMemory (which is a short rolling window fed back into the
prompt). This is an append-only audit log for debugging model behaviour.
"""

import json
from datetime import datetime
from pathlib import Path


class ConversationLog:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def record(self, prompt: str, raw_response: str, action: dict) -> None:
        """Append one prompt/response/action triple to the log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": raw_response,
            "action": action.get("action"),
            "reason": action.get("reason"),
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[ConversationLog] Warning: Failed to write: {e}")
