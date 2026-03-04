"""
action_specs.py — ActionSpec data class, all base action definitions,
prefab aliases, and the three pure helper functions that operate on them.

Single responsibility: define *what* each action needs and what it yields.
No game-state logic lives here.
"""

from dataclasses import dataclass


@dataclass
class ActionSpec:
    requires: dict[str, int]  # item → count needed
    provides: list[str]  # items this action can yield
    redundant_if_held: bool = False  # skip craft if output already in inventory


# ---------------------------------------------------------------------------
# Base action prerequisites and outputs
# "requires" uses inventory prefab names; count = minimum needed
# "provides" is informational (for future goal decomposition)
# ---------------------------------------------------------------------------
ACTION_SPECS: dict[str, ActionSpec] = {
    # Always valid
    "explore": ActionSpec(requires={}, provides=[]),
    "idle": ActionSpec(requires={}, provides=[]),
    # Survival — concrete variants generated from state at runtime
    "eat_food": ActionSpec(requires={}, provides=[]),  # generic fallback
    "run_from_enemy": ActionSpec(requires={}, provides=[]),
    # Tool-gated
    "chop_tree": ActionSpec(requires={"axe": 1}, provides=["log"]),
    "mine_rock": ActionSpec(requires={"pickaxe": 1}, provides=["rocks", "flint"]),
    # Crafting (consumes ingredients)
    # redundant_if_held=True → skip if you already own the output (one-off tools)
    "craft_item:axe": ActionSpec(
        requires={"twigs": 1, "flint": 1}, provides=["axe"], redundant_if_held=True
    ),
    "craft_item:pickaxe": ActionSpec(
        requires={"twigs": 2, "flint": 2}, provides=["pickaxe"], redundant_if_held=True
    ),
    "craft_item:campfire": ActionSpec(
        requires={"log": 2, "cutgrass": 3}, provides=["campfire"]
    ),
    "craft_item:torch": ActionSpec(
        requires={"twigs": 2, "cutgrass": 2}, provides=["torch"]
    ),
    "craft_item:firepit": ActionSpec(
        requires={"log": 2, "rocks": 12}, provides=["firepit"], redundant_if_held=True
    ),
    "craft_item:spear": ActionSpec(
        requires={"twigs": 2, "flint": 2, "rope": 1},
        provides=["spear"],
        redundant_if_held=True,
    ),
    "craft_item:rope": ActionSpec(requires={"cutgrass": 3}, provides=["rope"]),
    "craft_item:log_suit": ActionSpec(
        requires={"log": 8, "rope": 2}, provides=["log_suit"], redundant_if_held=True
    ),
    "craft_item:trap": ActionSpec(
        requires={"twigs": 2, "cutgrass": 3}, provides=["trap"]
    ),
    "craft_item:chest": ActionSpec(
        requires={"boards": 3}, provides=["treasurechest"], redundant_if_held=True
    ),
    "craft_item:boards": ActionSpec(requires={"log": 4}, provides=["boards"]),
}

# Canonical prefab aliases — only entries where the key differs from the value.
# normalize_inv falls back to the lowercased key when no alias is found.
PREFAB_ALIASES: dict[str, str] = {
    "twig": "twigs",
    "rock": "rocks",
}


# ---------------------------------------------------------------------------
# Pure helper functions — no class needed; tested directly
# ---------------------------------------------------------------------------


def normalize_inv(inv: dict[str, int]) -> dict[str, int]:
    """Map inventory keys to canonical prefab names, summing duplicates."""
    result: dict[str, int] = {}
    for key, count in inv.items():
        canonical = PREFAB_ALIASES.get(key.lower(), key.lower())
        result[canonical] = result.get(canonical, 0) + count
    return result


def has_prereqs(inv: dict[str, int], requires: dict[str, int]) -> bool:
    """Return True if *inv* (already normalised) satisfies all *requires*."""
    for item, needed in requires.items():
        canonical = PREFAB_ALIASES.get(item.lower(), item.lower())
        if inv.get(canonical, 0) < needed:
            return False
    return True


def missing_items(inv: dict[str, int], requires: dict[str, int]) -> dict[str, int]:
    """Return only the items and counts still needed from *requires*."""
    result: dict[str, int] = {}
    for item, needed in requires.items():
        canonical = PREFAB_ALIASES.get(item.lower(), item.lower())
        have = inv.get(canonical, 0)
        if have < needed:
            result[item] = needed - have
    return result
