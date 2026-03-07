"""
actions.py — Pydantic models for action-related data structures.

Defines schemas for action options, commands, and LLM response validation.
"""

from pydantic import BaseModel, Field, field_validator


class ActionOption(BaseModel):
    """A concrete action option presented to the LLM."""

    action: str = Field(
        description="Action name (e.g. 'pick_up_item', 'gather_resource')"
    )
    target: str | None = Field(
        default=None, description="Target specification with distance/details"
    )
    reason: str = Field(default="", description="Why this action is suggested")

    def __repr__(self) -> str:
        """Convert to human-readable format for prompt display."""
        if self.target:
            return f"{self.action}  (target: {self.target})"
        return self.action


class ActionCommand(BaseModel):
    """The LLM's chosen action + reasoning."""

    action: str = Field(description="Chosen action name")
    target: str | None = Field(default=None, description="Target if applicable")
    reason: str = Field(description="Why this action was chosen")

    def __repr__(self) -> str:
        """Convert to compact log format."""
        if self.target:
            return f"{self.action} -> {self.target}"
        return self.action


class ParsedAction(BaseModel):
    """Pydantic model for validating LLM JSON responses.

    Validates that ``action`` is a non-empty string and ``target`` is provided.
    If LLM provides ``targets`` array instead of ``target``, validation fails.
    """

    action: str
    target: str | None = None
    reason: str = "no reason given"

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
