"""
goals — Goal derivation package for the DS LLM agent.

Public API:
  GoalManager   — derives goals from game state + inventory
  Urgency       — urgency enum (CRITICAL / URGENT / MODERATE / LOW)
  ShortTermGoal — immediate situational goal
  MidTermGoal   — day/season progression context
  LongTermGoal  — season-level survival strategy
"""

from goals.manager import GoalManager
from goals.models import LongTermGoal, MidTermGoal, ShortTermGoal, Urgency

__all__ = [
    "GoalManager",
    "Urgency",
    "ShortTermGoal",
    "MidTermGoal",
    "LongTermGoal",
]
