"""
action_parser.py — Extracts a structured action dict from raw LLM text output.
"""

import json


_DEFAULT_ACTION = {"action": "idle", "reason": "No decision made (error or timeout)"}


class ActionParser:
    def parse(self, llm_output: str | None) -> dict:
        """
        Parse LLM output into {"action": ..., "reason": ...}.
        Falls back to idle on any failure.
        """
        if not llm_output:
            return _DEFAULT_ACTION

        output = llm_output.strip()

        # Fast path: output is clean JSON
        if output.startswith("{"):
            result = self._try_parse(output)
            if result:
                return result

        # Fallback: extract first {...} block from mixed text
        start = output.find("{")
        end = output.rfind("}") + 1
        if start != -1 and end > start:
            result = self._try_parse(output[start:end])
            if result:
                return result

        print(f"[ActionParser] Could not parse action. Raw: {output[:200]}")
        return _DEFAULT_ACTION

    # ------------------------------------------------------------------

    @staticmethod
    def _try_parse(text: str) -> dict | None:
        try:
            data = json.loads(text)
            if "action" in data:
                return {
                    "action": str(data["action"]),
                    "reason": str(data.get("reason", "no reason given")),
                }
        except json.JSONDecodeError:
            pass
        return None
