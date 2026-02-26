"""
prompt.py — Builds the LLM prompt from game state and memory.

Keeping prompt logic separate makes it easy to tune instructions
without touching agent plumbing.
"""

# Available actions surfaced to the LLM
ACTION_SPACE = [
    "move_to_food",
    "chop_tree",
    "mine_rock",
    "pick_up_item",
    "craft_item:NAME",
    "eat_food",
    "cook_food",
    "run_from_enemy",
    "attack_enemy",
    "explore",
    "idle",
]

CRITICAL_THRESHOLD = 50  # Health/hunger/sanity below this = urgent action required

# Crafting recipes: item -> {ingredient: count}
RECIPES: dict[str, dict[str, int]] = {
    "axe": {"twig": 1, "flint": 1},
    "pickaxe": {"twig": 2, "flint": 2},
    "campfire": {"log": 2, "cutgrass": 2},
    "torch": {"twig": 2, "cutgrass": 2},
}


def _parse_inv(state: dict) -> dict[str, int]:
    """Convert [\"log x20\", \"axe\"] -> {\"log\": 20, \"axe\": 1}."""
    result: dict[str, int] = {}
    for item in state.get("inventory", []):
        if " x" in item:
            name, _, count = item.rpartition(" x")
            result[name.strip()] = int(count)
        else:
            result[item.strip()] = 1
    return result


def _prerequisites_section(inv: dict[str, int]) -> str:
    """Return a concise tool-status + craftability block for the prompt."""
    lines = []

    # Key tools
    has_axe = "axe" in inv
    has_pickaxe = "pickaxe" in inv

    lines.append(
        f"  axe: {'✓ have it' if has_axe else '✗ missing — craft_item:axe needs 1 twig + 1 flint'}"
    )
    lines.append(
        f"  pickaxe: {'✓ have it' if has_pickaxe else '✗ missing — craft_item:pickaxe needs 2 twig + 2 flint'}"
    )

    # What the player can craft right now
    craftable = [
        name
        for name, recipe in RECIPES.items()
        if all(inv.get(ing, 0) >= qty for ing, qty in recipe.items())
    ]
    if craftable:
        lines.append(f"  Can craft now: {', '.join(craftable)}")

    # Action gating
    if not has_axe:
        lines.append("  ⚠ chop_tree requires an axe — craft or find one first")
    if not has_pickaxe:
        lines.append("  ⚠ mine_rock requires a pickaxe — craft or find one first")

    return "\n".join(lines)


SYSTEM_RULES = """Survive in the wild. Act only on CRITICAL stats (< 50). Priority order:
- Threats nearby → run_from_enemy
- Night (time > 0.75) + no light → craft_item:torch or campfire
- Any stat < 50 → address it
- Build tools (axe, pickaxe) to gather resources efficiently.
- Seasons change: autumn (safe) → winter (cold, scarce food) → spring (rain) → summer (heat)
- Missing axe → craft_item:axe (needs 1 twig + 1 flint) or gather ingredients
- Have axe → chop_tree
- Otherwise → explore
"""


def build_prompt(
    state: dict, memory: list[dict], inv: dict[str, int] | None = None
) -> str:
    """Build the full LLM prompt from current game state and recent memory.

    Args:
        state:  Raw game state dict from game_state.json.
        memory: Recent memory entries from AgentMemory.
        inv:    Pre-parsed inventory counts (avoids re-parsing if caller already has it).
    """

    # Recent memory — prefer inventory/event entries first, then llm_reason
    memory_lines = ""
    if memory:
        for entry in memory[-8:]:
            memory_lines += f"  - [{entry.get('source', 'event')}] {entry['text']}\n"

    # Threat summary
    threat_lines = ""
    if state.get("threats"):
        threat_lines = "\n".join(
            f"  ⚠ {t['name']} ({t.get('type', '?')}) at {t['distance']}m"
            for t in state["threats"]
        )

    # Critical stat warnings
    def stat_label(value, max_value):
        try:
            v = float(value)
            return f"{v:.0f}/{max_value} {'[CRITICAL]' if v < CRITICAL_THRESHOLD else '[OK]'}"
        except (TypeError, ValueError):
            return f"{value}/{max_value}"

    # Inventory — compact single line using parsed counts
    inv = inv if inv is not None else _parse_inv(state)
    inv_line = (
        ", ".join(
            f"{name} x{count}" if count > 1 else name
            for name, count in sorted(inv.items())
        )
        or "empty"
    )

    prerequisites = _prerequisites_section(inv)

    # Nearby entities (top 5)
    nearby_lines = (
        "\n".join(
            f"  • {e['name']} ({e['type']}) - {e['distance']}m"
            for e in state.get("nearby_entities", [])[:5]
        )
        or "  (none)"
    )

    action_list = ", ".join(ACTION_SPACE)

    return f"""{SYSTEM_RULES}

[STATUS]
  Day:{state.get("day", "?")} Time:{state.get("time_of_day", 0):.2f} Season:{state.get("season", "?")}
  Health:{stat_label(state.get("health"), 100)} Hunger:{stat_label(state.get("hunger"), 150)} Sanity:{stat_label(state.get("sanity"), 200)}
  Equipped:{state.get("equipped", "none")}
[/STATUS]

[INVENTORY]
  {inv_line}
[/INVENTORY]

[NEARBY]
{nearby_lines}
[/NEARBY]

[TOOLS]
{prerequisites}
[/TOOLS]
{"[THREATS]" + chr(10) + threat_lines + chr(10) + "[/THREATS]" + chr(10) if threat_lines else ""}[MEMORY]
{memory_lines.rstrip() or "  (none)"}
[/MEMORY]

Actions: {action_list}

Reply ONLY with JSON:
{{"action":"action_name","reason":"why"}}"""
