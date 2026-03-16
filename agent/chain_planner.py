"""
chain_planner.py — Computes unlock chains from ActionSpec data.

Given an item and current inventory, answers:
  "What could I craft if I pick this up?"
  "What capabilities would that unlock?"

This replaces hardcoded chain hints with data-driven computation.
No full GOAP planning yet — just forward-looking unlock chains.
"""

from action_specs import ACTION_SPECS, ActionSpec, has_prereqs, PREFAB_ALIASES


# Tools that unlock specific action capabilities
TOOL_CAPABILITIES: dict[str, list[str]] = {
    "axe": ["chop trees"],
    "pickaxe": ["mine rocks", "mine gold"],
    "shovel": ["dig"],
    "hammer": ["deconstruct"],
    "spear": ["hunt", "fight"],
}

# Items with special strategic value (not tool-based)
STRATEGIC_ITEMS: dict[str, str] = {
    "goldnugget": "science machines",
    "gears": "icebox/fridge",
    "silk": "tents, fishing rods",
    "papyrus": "books, birdcage",
}


def _normalize(item: str) -> str:
    """Normalize item name to canonical form."""
    return PREFAB_ALIASES.get(item.lower(), item.lower())


def _get_crafts_using(item: str) -> list[tuple[str, ActionSpec]]:
    """Find all craft actions that require this item."""
    item_norm = _normalize(item)
    results = []
    for action_name, spec in ACTION_SPECS.items():
        if not action_name.startswith("craft_item:"):
            continue
        for req_item in spec.requires:
            if _normalize(req_item) == item_norm:
                results.append((action_name, spec))
                break
    return results


def _get_tool_name(action_name: str) -> str | None:
    """Extract tool name from craft action like 'craft_item:axe' -> 'axe'."""
    if action_name.startswith("craft_item:"):
        return action_name.split(":")[1]
    return None


def get_unlock_chain(
    item: str,
    inv: dict[str, int],
    max_depth: int = 2,
) -> str:
    """
    Compute what picking up this item could unlock.

    Returns a chain hint like:
      "-> axe (missing) -> chop trees"
      "-> pickaxe, spear"
      ""  (empty if no interesting unlocks)

    Args:
        item: The item being picked up (e.g., "flint")
        inv: Current inventory
        max_depth: How deep to trace chains (default 2)
    """
    item_norm = _normalize(item)

    # Check if this is a strategic item with inherent value
    if item_norm in STRATEGIC_ITEMS:
        return f" -> {STRATEGIC_ITEMS[item_norm]}"

    # Find crafts this item enables
    crafts = _get_crafts_using(item)
    if not crafts:
        return ""

    # Filter to crafts we're missing ingredients for (interesting unlocks)
    # and crafts where we don't already have the output
    interesting_unlocks: list[str] = []

    for action_name, spec in crafts:
        tool = _get_tool_name(action_name)
        if not tool:
            continue

        # Skip if we already have this tool
        if inv.get(_normalize(tool), 0) > 0:
            continue

        # Check what we'd need after picking up this item
        future_inv = dict(inv)
        future_inv[item_norm] = future_inv.get(item_norm, 0) + 1

        # Get capabilities this tool would unlock
        capabilities = TOOL_CAPABILITIES.get(tool, [])

        if has_prereqs(future_inv, spec.requires):
            # We could craft it immediately after pickup
            if capabilities:
                interesting_unlocks.append(f"{tool} -> {', '.join(capabilities)}")
            else:
                interesting_unlocks.append(tool)
        else:
            # Still missing other ingredients
            if capabilities:
                interesting_unlocks.append(
                    f"{tool} (need more) -> {', '.join(capabilities)}"
                )

    if not interesting_unlocks:
        return ""

    # Take first 2 most interesting unlocks to keep prompt short
    return " -> " + "; ".join(interesting_unlocks[:2])


def get_pickup_hint(item: str, inv: dict[str, int]) -> str:
    """
    Get a hint for why picking up this item matters.

    This is the main entry point for action annotations.
    Returns empty string if no special hint needed.
    """
    return get_unlock_chain(item, inv)
