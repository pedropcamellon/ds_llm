"""
goap_executor.py — Translates strategic goals into concrete per-tick actions.

Given a goal (e.g., "prepare_light") and current state, computes:
  1. What sub-goals are needed (e.g., "have torch" → "have twigs + cutgrass")
  2. What's the NEXT action to take (e.g., "pick_up_item:twigs")

This runs every tick (fast, no LLM) while the strategic goal persists.
"""

from dataclasses import dataclass

from action_specs import ACTION_SPECS, has_prereqs, missing_items
from models import GameState, ActionOption


@dataclass
class GOAPPlan:
    """A computed plan to achieve a goal."""
    goal: str
    steps: list[str]  # Ordered action sequence
    next_action: ActionOption | None  # First executable action
    blocked_reason: str | None = None  # Why we can't proceed


# Goal -> What items/tools satisfy it
GOAL_REQUIREMENTS: dict[str, dict[str, any]] = {
    "prepare_light": {"items": ["torch", "campfire"], "any": True},
    "find_food": {"stats": {"hunger": 80}},
    "heal_up": {"stats": {"health": 80}},
    "flee_danger": {"conditions": {"threats_nearby": False}},
    "gather_basics": {"items": {"cutgrass": 6, "twigs": 6, "flint": 2}},
    "gather_wood": {"items": {"log": 10}},
    "gather_stone": {"items": {"rocks": 10}},
    "get_gold": {"items": {"goldnugget": 2}},
    "craft_tools": {"items": ["axe", "pickaxe"], "any": False},
    "build_firepit": {"items": ["firepit"]},
    "build_science": {"items": ["science_machine"]},
    "explore_area": {},  # Never complete
    "find_base_spot": {},  # Never complete
}

# How to get specific items (material -> action)
ITEM_SOURCES: dict[str, list[str]] = {
    "cutgrass": ["pick_up_item", "gather_resource"],
    "twigs": ["pick_up_item", "gather_resource"],
    "flint": ["pick_up_item", "mine_rock"],
    "log": ["chop_tree", "pick_up_item"],
    "rocks": ["mine_rock", "pick_up_item"],
    "goldnugget": ["mine_rock"],
    "torch": ["craft_item:torch"],
    "campfire": ["craft_item:campfire"],
    "axe": ["craft_item:axe"],
    "pickaxe": ["craft_item:pickaxe"],
    "firepit": ["craft_item:firepit"],
}


def is_goal_satisfied(goal: str, state: GameState, inv: dict[str, int]) -> bool:
    """Check if a goal is already satisfied."""
    reqs = GOAL_REQUIREMENTS.get(goal, {})
    
    if not reqs:
        return False  # Goals like "explore" are never satisfied
    
    # Check item requirements
    if "items" in reqs:
        items = reqs["items"]
        any_mode = reqs.get("any", False)
        
        if isinstance(items, list):
            # List of items — check if we have any/all
            has_items = [inv.get(item, 0) > 0 for item in items]
            if any_mode:
                return any(has_items)
            return all(has_items)
        elif isinstance(items, dict):
            # Dict with counts — check if we have enough
            for item, count in items.items():
                if inv.get(item, 0) < count:
                    return False
            return True
    
    # Check stat requirements
    if "stats" in reqs:
        for stat, threshold in reqs["stats"].items():
            actual = getattr(state, stat, 0)
            if actual < threshold:
                return False
        return True
    
    return False


def get_next_action_for_goal(
    goal: str,
    state: GameState,
    inv: dict[str, int],
    nearby_items: list[str],
) -> GOAPPlan:
    """Compute the next action to take toward a goal.
    
    Args:
        goal: Strategic goal name
        state: Current game state
        inv: Current inventory
        nearby_items: Items visible nearby (from state.nearby_entities)
    
    Returns:
        GOAPPlan with next_action if one is available
    """
    if is_goal_satisfied(goal, state, inv):
        return GOAPPlan(
            goal=goal,
            steps=["COMPLETE"],
            next_action=None,
            blocked_reason="Goal already satisfied",
        )
    
    reqs = GOAL_REQUIREMENTS.get(goal, {})
    steps: list[str] = []
    
    # Determine what we need
    if "items" in reqs:
        items = reqs["items"]
        if isinstance(items, list):
            # Find first item we're missing
            for item in items:
                if inv.get(item, 0) == 0:
                    return _plan_to_get_item(goal, item, state, inv, nearby_items)
        elif isinstance(items, dict):
            # Find first item we need more of
            for item, count in items.items():
                if inv.get(item, 0) < count:
                    return _plan_to_get_item(goal, item, state, inv, nearby_items)
    
    # Stat goals — find food or healing items
    if "stats" in reqs:
        if "hunger" in reqs["stats"] and state.hunger < reqs["stats"]["hunger"]:
            return _plan_to_eat(goal, state, inv, nearby_items)
        if "health" in reqs["stats"] and state.health < reqs["stats"]["health"]:
            return _plan_to_heal(goal, state, inv, nearby_items)
    
    # Flee goal
    if goal == "flee_danger":
        return GOAPPlan(
            goal=goal,
            steps=["run_from_enemy"],
            next_action=ActionOption(
                action="run_from_enemy",
                target="away",
                reason="Fleeing from threat",
            ),
        )
    
    # Explore goal
    if goal in ("explore_area", "find_base_spot"):
        return GOAPPlan(
            goal=goal,
            steps=["explore"],
            next_action=ActionOption(
                action="explore",
                target="N",  # Will be refined by concrete action builder
                reason="Exploring the area",
            ),
        )
    
    return GOAPPlan(
        goal=goal,
        steps=[],
        next_action=None,
        blocked_reason=f"No plan found for goal: {goal}",
    )


def _plan_to_get_item(
    goal: str,
    item: str,
    state: GameState,
    inv: dict[str, int],
    nearby_items: list[str],
) -> GOAPPlan:
    """Plan how to get a specific item."""
    sources = ITEM_SOURCES.get(item, [])
    
    for source in sources:
        if source == "pick_up_item":
            # Check if item is nearby
            for nearby in nearby_items:
                if item.lower() in nearby.lower():
                    return GOAPPlan(
                        goal=goal,
                        steps=[f"pick_up_item:{nearby}"],
                        next_action=ActionOption(
                            action="pick_up_item",
                            target=nearby,
                            reason=f"Getting {item} for {goal}",
                        ),
                    )
        
        elif source == "gather_resource":
            # Check if resource is nearby
            for nearby in nearby_items:
                if item.lower() in nearby.lower():
                    return GOAPPlan(
                        goal=goal,
                        steps=[f"gather_resource:{nearby}"],
                        next_action=ActionOption(
                            action="gather_resource",
                            target=nearby,
                            reason=f"Gathering {item} for {goal}",
                        ),
                    )
        
        elif source.startswith("craft_item:"):
            craft_name = source
            spec = ACTION_SPECS.get(craft_name)
            if spec and has_prereqs(inv, spec.requires):
                return GOAPPlan(
                    goal=goal,
                    steps=[craft_name],
                    next_action=ActionOption(
                        action="craft_item",
                        target=item,
                        reason=f"Crafting {item} for {goal}",
                    ),
                )
            elif spec:
                # Need to get ingredients first
                missing = missing_items(inv, spec.requires)
                first_missing = list(missing.keys())[0]
                return _plan_to_get_item(goal, first_missing, state, inv, nearby_items)
        
        elif source == "chop_tree":
            if inv.get("axe", 0) > 0:
                # Find nearby tree
                for nearby in nearby_items:
                    if "tree" in nearby.lower() or "evergreen" in nearby.lower():
                        return GOAPPlan(
                            goal=goal,
                            steps=["chop_tree"],
                            next_action=ActionOption(
                                action="chop_tree",
                                target=nearby,
                                reason=f"Chopping for logs ({goal})",
                            ),
                        )
            else:
                # Need axe first
                return _plan_to_get_item(goal, "axe", state, inv, nearby_items)
        
        elif source == "mine_rock":
            if inv.get("pickaxe", 0) > 0:
                # Find nearby rock
                for nearby in nearby_items:
                    if "rock" in nearby.lower() or "boulder" in nearby.lower():
                        return GOAPPlan(
                            goal=goal,
                            steps=["mine_rock"],
                            next_action=ActionOption(
                                action="mine_rock",
                                target=nearby,
                                reason=f"Mining for {item} ({goal})",
                            ),
                        )
            else:
                # Need pickaxe first
                return _plan_to_get_item(goal, "pickaxe", state, inv, nearby_items)
    
    # Can't find a way to get this item — explore
    return GOAPPlan(
        goal=goal,
        steps=["explore"],
        next_action=ActionOption(
            action="explore",
            target="N",
            reason=f"Looking for {item} ({goal})",
        ),
    )


def _plan_to_eat(
    goal: str,
    state: GameState,
    inv: dict[str, int],
    nearby_items: list[str],
) -> GOAPPlan:
    """Plan to restore hunger."""
    # Check inventory for edibles
    edibles = ["berries", "carrot", "seeds", "meat", "cooked"]
    for item, count in inv.items():
        if count > 0 and any(e in item.lower() for e in edibles):
            return GOAPPlan(
                goal=goal,
                steps=[f"eat_food:{item}"],
                next_action=ActionOption(
                    action="eat_food",
                    target=item,
                    reason="Eating to restore hunger",
                ),
            )
    
    # Look for food nearby
    for nearby in nearby_items:
        if any(e in nearby.lower() for e in edibles):
            return GOAPPlan(
                goal=goal,
                steps=[f"pick_up_item:{nearby}", "eat_food"],
                next_action=ActionOption(
                    action="pick_up_item",
                    target=nearby,
                    reason="Getting food to eat",
                ),
            )
    
    return GOAPPlan(
        goal=goal,
        steps=["explore"],
        next_action=ActionOption(
            action="explore",
            target="N",
            reason="Looking for food",
        ),
    )


def _plan_to_heal(
    goal: str,
    state: GameState,
    inv: dict[str, int],
    nearby_items: list[str],
) -> GOAPPlan:
    """Plan to restore health."""
    # Healing = eat food (in DS, eating restores health)
    return _plan_to_eat(goal, state, inv, nearby_items)
