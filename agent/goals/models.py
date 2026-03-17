"""
goals/models.py — Data models for the goal system.

Enums and dataclasses representing long-term, mid-term, and short-term survival
goals. These are pure data — no game-state logic lives here.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

# Type alias for predicates (avoid circular import by using TYPE_CHECKING)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.state import GameState

Predicate = Callable[["GameState"], bool] | None


class Urgency(Enum):
    CRITICAL = 0
    URGENT = 1
    MODERATE = 2
    LOW = 3


@dataclass
class ShortTermGoal:
    urgency: Urgency
    description: str
    preferred_actions: list[str]
    reason: str = ""
    goal_check: Predicate = None


@dataclass
class MidTermGoal:
    """Day-based progression context (plan for today)."""

    day_range: str  # "Day 1", "Day 2-3", etc.
    description: str
    focus_actions: list[str]  # Actions that help achieve this goal
    reason: str
    goal_check: Predicate = None


@dataclass
class LongTermGoal:
    season: str
    description: str
    focus_actions: list[str] = field(default_factory=list)
    goal_check: Predicate = None


@dataclass
class ActiveGoal:
    """Wrapper for a selected mid-term goal with selection metadata.

    Tracks when the goal was selected to enable timeout-based reselection
    and completion analytics.
    """

    goal: MidTermGoal
    selected_day: int  # Game day when goal was selected
    selected_phase: str  # Phase when selected ("day", "dusk", "night")
    selection_reason: str = ""  # LLM's explanation for choosing this goal
