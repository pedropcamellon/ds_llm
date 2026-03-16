"""
prereq_resolver.py — Core GOAP prerequisite dependency resolver.

Given a goal or target item, computes the backward dependency chain until
an immediately achievable action is found. This is the "planning" layer.
"""

import logging
from dataclasses import dataclass
from models.state import GameState, NearbyEntity
from models.actions import ActionCommand
from strategic_goals import get_goal_description, _GOAL_CATALOG
from ds_recipes import RECIPES
from entity_sets import (
    HARVESTABLE_ENTITIES,
    HARVEST_REQUIRES_TOOL,
    PICKUP_PREFABS,
)

logger = logging.getLogger(__name__)


@dataclass
class PrereqStep:
    """A single step in the prerequisite chain."""

    item: str
    source: str  # "craft", "pickup", "harvest", "mine", "chop"
    quantity_needed: int = 1


# Build recipe lookup dict once at module load
_RECIPE_MAP: dict[str, dict] = {r["name"]: r for r in RECIPES}


def resolve_next_action(
    goal_id: str, state: GameState, inv: dict[str, int]
) -> ActionCommand:
    """
    Main orchestrator: resolve next achievable action for a goal.

    Args:
        goal_id: Strategic goal identifier (e.g., "gather_basic_resources")
        state: Current game state
        inv: Normalized inventory dict (item -> count)

    Returns:
        ActionCommand for the next action to take, or explore as fallback
    """
    if goal_id not in _GOAL_CATALOG:
        logger.warning(f"Unknown goal_id: {goal_id}, falling back to explore")
        return ActionCommand(
            action="explore",
            target=None,
            reason=f"Unknown goal: {goal_id}",
        )

    goal_data = _GOAL_CATALOG[goal_id]
    completion_items = goal_data["completion_items"]

    # Special case: goals with no completion items (open-ended like explore)
    if not completion_items:
        return ActionCommand(
            action="explore",
            target=None,
            reason=f"Goal '{goal_id}' has no specific items to obtain",
        )

    # Find first missing item and resolve its prerequisites
    for item in completion_items:
        if inv.get(item, 0) < 1:
            logger.info(f"Goal '{goal_id}' needs item: {item}")

            # Try to find immediate action for this item
            action = _resolve_item(item, state, inv)
            if action:
                return ActionCommand(
                    action=action["action"],
                    target=action.get("target"),
                    reason=f"Working toward goal '{goal_id}': need {item}",
                )

    # All items present — goal should be complete
    logger.info(f"Goal '{goal_id}' appears complete, defaulting to explore")
    return ActionCommand(
        action="explore",
        target=None,
        reason=f"Goal '{goal_id}' completion items all present",
    )


def get_prereq_chain(item: str, inv: dict[str, int]) -> list[PrereqStep]:
    """
    Build prerequisite chain for an item (recursive backward lookup).

    Args:
        item: Target item name
        inv: Current inventory

    Returns:
        List of PrereqStep objects showing dependency path
    """
    chain: list[PrereqStep] = []
    _build_chain_recursive(item, inv, chain, visited=set())
    return chain


def _build_chain_recursive(
    item: str,
    inv: dict[str, int],
    chain: list[PrereqStep],
    visited: set[str],
    depth: int = 0,
) -> None:
    """Recursively build prerequisite chain, detecting circular dependencies."""

    # Circular dependency detection
    if item in visited or depth > 10:
        logger.warning(f"Circular dependency or max depth for {item}")
        return

    visited.add(item)

    # If already have item, no prereqs needed
    if inv.get(item, 0) >= 1:
        return

    # Check if craftable
    if item in _RECIPE_MAP:
        recipe = _RECIPE_MAP[item]
        chain.append(PrereqStep(item=item, source="craft"))

        # Add ingredient prereqs
        for ingredient, qty in recipe["ingredients"].items():
            if inv.get(ingredient, 0) < qty:
                _build_chain_recursive(ingredient, inv, chain, visited, depth + 1)
        return

    # Check if it's a harvestable yield (ground pickup or harvest)
    # For simplicity, mark as "pickup" if it's in PICKUP_PREFABS
    if item in PICKUP_PREFABS:
        chain.append(PrereqStep(item=item, source="pickup"))
        return

    # Check if it's obtainable by harvesting an entity
    for entity_name, yield_item in HARVESTABLE_ENTITIES.items():
        if yield_item == item:
            # Determine source type based on tool requirement
            if entity_name in HARVEST_REQUIRES_TOOL:
                tool = HARVEST_REQUIRES_TOOL[entity_name]
                if tool == "axe":
                    source = "chop"
                elif tool == "pickaxe":
                    source = "mine"
                else:
                    source = "harvest"
            else:
                source = "harvest"

            chain.append(PrereqStep(item=item, source=source))

            # If tool required, add tool as prereq
            if entity_name in HARVEST_REQUIRES_TOOL:
                tool = HARVEST_REQUIRES_TOOL[entity_name]
                if inv.get(tool, 0) < 1:
                    _build_chain_recursive(tool, inv, chain, visited, depth + 1)
            return

    # No known path to obtain this item
    logger.warning(f"No known path to obtain item: {item}")


def can_achieve_now(action: dict, state: GameState, inv: dict[str, int]) -> bool:
    """
    Check if an action is immediately executable in current state.

    Args:
        action: Action dict with "action" and optional "target" keys
        state: Current game state
        inv: Current inventory

    Returns:
        True if action can be executed right now
    """
    action_name = action["action"]
    target = action.get("target")

    # Explore is always achievable
    if action_name == "explore":
        return True

    # pick_up_item: check if item is nearby
    if action_name == "pick_up_item":
        if not target:
            return False
        # Check nearby_entities for this item
        for entity in state.nearby_entities:
            if entity.name == target and entity.distance < 20:
                return True
        return False

    # gather_resource / harvest: check if harvestable entity nearby
    if action_name in ["gather_resource", "harvest"]:
        if not target:
            return False
        # Check if target entity nearby
        for entity in state.nearby_entities:
            if entity.name == target and entity.distance < 20:
                # Check tool requirement
                if target in HARVEST_REQUIRES_TOOL:
                    required_tool = HARVEST_REQUIRES_TOOL[target]
                    if inv.get(required_tool, 0) < 1:
                        return False  # Missing required tool
                return True
        return False

    # chop: requires axe and tree nearby
    if action_name == "chop":
        if inv.get("axe", 0) < 1:
            return False  # No axe
        if not target:
            return False
        # Check if tree nearby
        tree_prefabs = [
            "evergreen",
            "birchnutt_tree",
            "lumpy_evergreen",
            "deciduoustree",
        ]
        for entity in state.nearby_entities:
            if entity.name in tree_prefabs and entity.distance < 20:
                return True
        return False

    # mine: requires pickaxe and boulder nearby
    if action_name == "mine":
        if inv.get("pickaxe", 0) < 1:
            return False  # No pickaxe
        if not target:
            return False
        # Check if boulder nearby
        boulder_prefabs = ["rock1", "rock2", "rock_flintless", "rock_flint", "rock_ore"]
        for entity in state.nearby_entities:
            if entity.name in boulder_prefabs and entity.distance < 20:
                return True
        return False

    # craft: check if have all ingredients
    if action_name == "craft":
        if not target:
            return False
        if target not in _RECIPE_MAP:
            return False

        recipe = _RECIPE_MAP[target]
        for ingredient, qty in recipe["ingredients"].items():
            if inv.get(ingredient, 0) < qty:
                return False  # Missing ingredient
        return True

    # Default: unknown action, assume not achievable
    logger.warning(f"Unknown action type for achievability check: {action_name}")
    return False


# --- Private helper functions ---


def _resolve_item(item: str, state: GameState, inv: dict[str, int]) -> dict | None:
    """
    Find next immediate action to obtain an item.

    Returns action dict {"action": str, "target": str} or None if no path found.
    """
    # Check if item is on ground nearby (highest priority - simplest action)
    for entity in state.nearby_entities:
        if entity.name == item and entity.distance < 20:
            return {"action": "pick_up_item", "target": item}

    # Check if item is harvestable from a nearby entity
    for entity in state.nearby_entities:
        if entity.name in HARVESTABLE_ENTITIES:
            yield_item = HARVESTABLE_ENTITIES[entity.name]
            if yield_item == item and entity.distance < 20:
                # Check tool requirement
                if entity.name in HARVEST_REQUIRES_TOOL:
                    required_tool = HARVEST_REQUIRES_TOOL[entity.name]
                    if inv.get(required_tool, 0) < 1:
                        # Need tool first — recurse to resolve tool
                        return _resolve_item(required_tool, state, inv)

                # Determine action type
                if entity.name in HARVEST_REQUIRES_TOOL:
                    tool = HARVEST_REQUIRES_TOOL[entity.name]
                    if tool == "axe":
                        return {"action": "chop", "target": entity.name}
                    elif tool == "pickaxe":
                        return {"action": "mine", "target": entity.name}

                return {"action": "harvest", "target": entity.name}

    # Check if item is craftable
    if item in _RECIPE_MAP:
        recipe = _RECIPE_MAP[item]

        # Check if have all ingredients
        missing_ingredients = []
        for ingredient, qty in recipe["ingredients"].items():
            if inv.get(ingredient, 0) < qty:
                missing_ingredients.append(ingredient)

        if not missing_ingredients:
            # Can craft now
            return {"action": "craft", "target": item}

        # Need to gather ingredients first — resolve first missing ingredient
        first_missing = missing_ingredients[0]
        return _resolve_item(first_missing, state, inv)

    # No path found — need to explore to find resources
    logger.info(f"No immediate path to obtain {item}, suggesting explore")
    return {"action": "explore", "target": None}
