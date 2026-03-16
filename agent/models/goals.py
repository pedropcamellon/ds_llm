"""
goals.py — Pydantic models for strategic goal definitions.

Strategic goals represent high-level objectives that take multiple ticks to complete.
"""

from pydantic import BaseModel, Field


class StrategicGoal(BaseModel):
    """A high-level strategic objective for the LLM to choose from.
    
    Goals are filtered based on game state and presented to the LLM.
    The LLM picks one goal, and GOAP resolves it into concrete actions.
    """
    
    id: str = Field(description="Unique goal identifier (e.g., 'gather_basic_resources')")
    description: str = Field(description="Human-readable one-line description for LLM prompt")
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority ranking (1=most urgent, 10=least urgent)"
    )
    completion_items: list[str] = Field(
        default_factory=list,
        description="List of items/conditions that mark goal as complete"
    )
    
    def __str__(self) -> str:
        """Format for LLM prompt: 'id — description'."""
        return f"{self.id} — {self.description}"
