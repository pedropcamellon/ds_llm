"""goal_planner.py — backwards-compatibility shim. Use action_planner.ActionPlanner."""
# ruff: noqa: F401
from action_planner import ActionPlanner as GoalPlanner  # noqa: F401

__all__ = ["GoalPlanner"]

