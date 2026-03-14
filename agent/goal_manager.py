"""Backward-compat shim — re-exports from goals package."""

from goals import GoalManager, LongTermGoal, MidTermGoal, ShortTermGoal, Urgency

__all__ = ["GoalManager", "Urgency", "ShortTermGoal", "MidTermGoal", "LongTermGoal"]
