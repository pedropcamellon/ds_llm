"""
strategic_goals.py — Strategic goal enumeration and filtering.

Defines high-level goals the LLM can choose from. Goals are filtered based on
current game state so the LLM only sees relevant, achievable objectives.
"""

import logging
from models.goals import StrategicGoal
from models.state import GameState

logger = logging.getLogger(__name__)


# Goal catalog: defines all strategic goals and their properties
_GOAL_CATALOG = {
    "gather_basic_resources": {
        "description": "Collect twigs, flint, grass to craft essential tools (axe, pickaxe, torch)",
        "priority": 2,
        "completion_items": ["axe", "pickaxe", "cutgrass"],
    },
    "prepare_for_night": {
        "description": "Ensure light source before darkness (craft torch or find campfire)",
        "priority": 1,  # Most urgent
        "completion_items": ["torch"],  # Simplification: having torch means prepared
    },
    "prepare_for_winter": {
        "description": "Gather warm gear and fuel stockpile for winter survival",
        "priority": 3,
        "completion_items": [
            "thermal_stone",
            "winter_hat",
            "log",
        ],  # log as proxy for stockpile
    },
    "establish_base": {
        "description": "Build permanent structures (firepit, science machine) for crafting",
        "priority": 4,
        "completion_items": [
            "firepit",
            "science_machine",
        ],  # These would be world state, simplified
    },
    "explore_new_area": {
        "description": "Discover map, find new biomes and resource locations",
        "priority": 7,
        "completion_items": [],  # Time-based or biome-discovery based
    },
    "stockpile_food": {
        "description": "Gather and cook food for reserves (target: 10+ cooked items)",
        "priority": 5,
        "completion_items": ["cooked_meat", "berries"],  # Proxies for food count
    },
    "hunt_for_meat": {
        "description": "Kill passive animals for meat (rabbits, birds)",
        "priority": 6,
        "completion_items": ["spear", "meat"],
    },
}


def get_suggested_goals(state: GameState, inv: dict[str, int]) -> list[StrategicGoal]:
    """
    Return list of valid strategic goals for current state, ordered by priority.

    Args:
        state: Current game state
        inv: Normalized inventory dict (item name -> count)

    Returns:
        List of StrategicGoal objects, ordered by priority (most urgent first)
    """
    goals: list[StrategicGoal] = []

    # Filter each goal by its validity conditions
    for goal_id, goal_data in _GOAL_CATALOG.items():
        if _is_goal_valid(goal_id, state, inv):
            goals.append(
                StrategicGoal(
                    id=goal_id,
                    description=goal_data["description"],
                    priority=goal_data["priority"],
                    completion_items=goal_data["completion_items"],
                )
            )

    # Sort by priority (lower number = higher urgency)
    goals.sort(key=lambda g: g.priority)

    logger.info(
        f"Suggested {len(goals)} goals for phase={state.phase}, day={state.day}"
    )
    return goals


def is_goal_complete(goal_id: str, state: GameState, inv: dict[str, int]) -> bool:
    """
    Check if a strategic goal's completion conditions are met.

    Args:
        goal_id: Goal identifier string
        state: Current game state
        inv: Normalized inventory dict

    Returns:
        True if goal is complete, False otherwise
    """
    if goal_id not in _GOAL_CATALOG:
        logger.warning(f"Unknown goal_id: {goal_id}")
        return False

    goal_data = _GOAL_CATALOG[goal_id]
    completion_items = goal_data["completion_items"]

    # Special case: goals with no completion items (time-based or open-ended)
    if not completion_items:
        return False  # Never auto-complete explore_new_area

    # Check if all completion items are in inventory
    for item in completion_items:
        if item not in inv or inv[item] < 1:
            return False

    return True


def get_goal_description(goal_id: str) -> str:
    """Get human-readable description for a goal ID."""
    if goal_id not in _GOAL_CATALOG:
        return f"Unknown goal: {goal_id}"
    return _GOAL_CATALOG[goal_id]["description"]


# --- Private filtering functions ---


def _is_goal_valid(goal_id: str, state: GameState, inv: dict[str, int]) -> bool:
    """Check if a goal is valid for current state."""

    # gather_basic_resources: valid on days 1-3 if missing essential tools
    if goal_id == "gather_basic_resources":
        if state.day > 3:
            return False  # Too late, should have tools by now
        # Valid if missing axe OR pickaxe
        has_axe = inv.get("axe", 0) > 0
        has_pickaxe = inv.get("pickaxe", 0) > 0
        return not (has_axe and has_pickaxe)

    # prepare_for_night: valid in dusk or late day
    if goal_id == "prepare_for_night":
        if state.phase == "dusk":
            return True
        if state.phase == "day" and state.time_of_day > 0.7:
            return True  # Late afternoon
        # Also valid at night if don't have torch equipped
        if state.phase == "night" and state.equipped != "torch":
            return True
        return False

    # prepare_for_winter: valid in late autumn (days 10-16)
    if goal_id == "prepare_for_winter":
        if state.season.lower() != "autumn":
            return False
        return state.day >= 10  # Last ~6 days of autumn

    # establish_base: valid if have tools but no base structures
    if goal_id == "establish_base":
        has_axe = inv.get("axe", 0) > 0
        has_pickaxe = inv.get("pickaxe", 0) > 0
        if not (has_axe and has_pickaxe):
            return False  # Need tools first
        # Simplified: assume no base yet (would check world state in full version)
        has_firepit = inv.get("firepit", 0) > 0
        return not has_firepit

    # explore_new_area: always valid as fallback (low priority)
    if goal_id == "explore_new_area":
        return True

    # stockpile_food: valid if hunger < 100 or low food count
    if goal_id == "stockpile_food":
        if state.hunger < 100:
            return True
        # Approximation: check if have < 5 edible items
        food_count = sum(
            count
            for item, count in inv.items()
            if item in ["berries", "cooked_meat", "carrot", "seeds"]
        )
        return food_count < 5

    # hunt_for_meat: valid if have weapon and low meat
    if goal_id == "hunt_for_meat":
        has_weapon = inv.get("spear", 0) > 0 or inv.get("axe", 0) > 0
        if not has_weapon:
            return False
        meat_count = inv.get("meat", 0) + inv.get("cooked_meat", 0)
        return meat_count < 3

    # Unknown goal: reject
    return False


def format_goals_for_prompt(goals: list[StrategicGoal], max_goals: int = 5) -> str:
    """Format suggested goals for the LLM prompt."""
    if not goals:
        return "  No specific goals suggested — explore or gather resources."

    lines = []
    for goal in goals[:max_goals]:
        lines.append(f"  {goal.name}: {goal.description}")
    return "\n".join(lines)
