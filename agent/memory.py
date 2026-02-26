"""
memory.py — Persistent JSONL memory of agent decisions and game events.
"""

import json
from datetime import datetime
from pathlib import Path


class AgentMemory:
    def __init__(self, memory_file: Path, max_entries: int = 20):
        self.memory_file = memory_file
        self.max_entries = max_entries
        self._entries: list[dict] = []
        self._load()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add(self, text: str, source: str = "event") -> None:
        """Append a new entry and persist it."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "source": source,
        }
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)
        self._append(entry)

    def recent(self, n: int = 20) -> list[dict]:
        """Return the n most recent entries."""
        return self._entries[-n:]

    def clear(self) -> None:
        """Clear in-memory entries (does not truncate the file)."""
        self._entries = []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self.memory_file.exists():
            return
        try:
            with open(self.memory_file, "r") as f:
                for line in f:
                    if line.strip():
                        self._entries.append(json.loads(line))
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries :]
            print(f"[AgentMemory] Loaded {len(self._entries)} entries")
        except Exception as e:
            print(f"[AgentMemory] Warning: Failed to load memory: {e}")

    def _append(self, entry: dict) -> None:
        try:
            with open(self.memory_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[AgentMemory] Warning: Failed to persist entry: {e}")
