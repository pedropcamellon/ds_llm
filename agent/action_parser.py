"""
action_parser.py — Extracts a structured action dict from raw LLM text output.

The LLM may return extra context fields alongside ``action`` and ``reason``
(e.g. ``"target": "berries"``, ``"direction": "north"``). All such fields are
forwarded so callers and the Lua executor can make use of them.
"""

import json
import re

from pydantic import BaseModel, field_validator


_DEFAULT_ACTION = {"action": "idle", "reason": "No decision made (error or timeout)"}

# Characters LLMs sometimes emit between the last value and the closing }
_JUNK_BEFORE_BRACE = re.compile(r'(?<=["\d])\s*[);\.,!]+\s*(?=\})')

# Fields we always keep; anything else the LLM supplies is forwarded too
_REQUIRED_FIELDS = {"action", "reason"}


class ParsedAction(BaseModel):
    """Pydantic model for the LLM JSON response.

    Validates that ``action`` is a non-empty string. Extra fields
    (``target``, ``direction``, etc.) are forwarded unchanged via ``extra="allow"``.
    If ``action`` has no ``:target`` suffix the agent will resolve it to the
    first matching concrete action from the valid-action list.
    """

    action: str
    reason: str = "no reason given"

    model_config = {"extra": "allow"}

    @field_validator("action")
    @classmethod
    def action_must_be_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("action must not be empty")
        return v

    def to_dict(self) -> dict:
        """Return all fields (including extras) as a plain dict."""
        return self.model_dump()


class ActionParser:
    def parse(self, llm_output: str | None) -> dict:
        """
        Parse LLM output into {\"action\": ..., \"reason\": ..., <extra fields>}.
        Falls back to idle on any failure.
        Extra fields beyond ``action``/``reason`` are passed through unchanged.
        """
        if not llm_output:
            return _DEFAULT_ACTION

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
        return _DEFAULT_ACTION

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
            return parsed.to_dict()
        except Exception:
            pass
        return None
