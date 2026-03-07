"""
action_parser.py — Extracts a structured action dict from raw LLM text output.

The LLM returns action, target (optional), and reason. All fields are validated
using Pydantic and forwarded to the executor.
"""

import json
import logging
import random
import re

from models import ParsedAction

logger = logging.getLogger(__name__)


def _default_action() -> dict:
    """Return explore with random direction to avoid directional bias."""

    logger.warning("LLM output is empty or None, defaulting to explore action")

    directions = ["N", "S", "E", "W", "NE", "NW", "SE", "SW"]
    return {
        "action": "explore",
        "target": random.choice(directions),
        "reason": "No decision made (error or timeout)",
    }


# Characters LLMs sometimes emit between the last value and the closing }
_JUNK_BEFORE_BRACE = re.compile(r'(?<=["\d])\s*[);\.,!]+\s*(?=\})')


class ActionParser:
    def parse(self, llm_output: str | None) -> dict:
        """
        Parse LLM output into {\"action\": ..., \"reason\": ..., <extra fields>}.
        Falls back to explore on any failure.
        Extra fields beyond ``action``/``reason`` are passed through unchanged.
        """
        if not llm_output:
            return _default_action()

        output = llm_output.strip()

        # Fast path: output is clean JSON
        if output.startswith("{"):
            result = self._try_parse(output) or self._try_parse(self._clean(output))
            if result:
                return result

        # Fallback: extract first {...} block from mixed text
        start = output.find("{")
        end = output.rfind("}") + 1
        if start != -1 and end > start:
            candidate = output[start:end]
            result = self._try_parse(candidate) or self._try_parse(
                self._clean(candidate)
            )
            if result:
                return result

        print(f"[ActionParser] Could not parse action. Raw: {output[:200]}")
        return _default_action()

    # ------------------------------------------------------------------

    @staticmethod
    def _clean(text: str) -> str:
        """Remove common LLM junk characters that appear just before closing }."""
        return _JUNK_BEFORE_BRACE.sub("", text)

    @staticmethod
    def _try_parse(text: str) -> dict | None:
        try:
            data = json.loads(text)
            parsed = ParsedAction.model_validate(data)
            result = parsed.to_dict()
            return result

        except Exception:
            logger.error("Failed to parse action", exc_info=True)
