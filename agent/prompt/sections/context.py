"""
context.py — Pydantic model for prompt context.
"""

from pydantic import BaseModel, Field

from models import GameState, ActionOption


class PromptContext(BaseModel):
    """Type-safe context passed to all prompt sections."""

    state: GameState = Field(description="Current game state")
    current_turn_actions: list[ActionOption] = Field(
        default_factory=list, description="Valid actions for this turn"
    )
    goals: str = Field(default="", description="Formatted goals text")
    memory: list[dict] = Field(default_factory=list, description="Recent memory entries")
    last_action: str | None = Field(default=None, description="Previous action")
    last_action_changed: bool | None = Field(
        default=None, description="Whether last action had effect"
    )
    world_history: str = Field(
        default="", description="Recently seen entities now out of view"
    )
