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
    "axe":      {"twig": 1, "flint": 1},
    "pickaxe":  {"twig": 2, "flint": 2},
    "campfire": {"log": 2, "cutgrass": 2},
    "torch":    {"twig": 2, "cutgrass": 2},
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

    lines.append(f"  axe: {'✓ have it' if has_axe else '✗ missing — craft_item:axe needs 1 twig + 1 flint'}")
    lines.append(f"  pickaxe: {'✓ have it' if has_pickaxe else '✗ missing — craft_item:pickaxe needs 2 twig + 2 flint'}")

    # What the player can craft right now
    craftable = [
        name for name, recipe in RECIPES.items()
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

SYSTEM_RULES = """You are Wilson in Don't Starve. You must survive by gathering resources, cooking food, and managing your health.

CRITICAL RULES:
- DARKNESS KILLS YOU. Always have a fire before night or you die.
- Stats below 50 are CRITICAL and require immediate action. Stats above 50 are safe — do not waste food or resources.
- Hunger max is 150. Only eat if hunger < 50. Eating at 119/150 is wasteful.
- Health max is 100. Only heal if health < 50.
- Sanity max is 200. Only address sanity if sanity < 50.
- Build tools (axe, pickaxe) to gather resources efficiently.
- Seasons change: autumn (safe) → winter (cold, scarce food) → spring (rain) → summer (heat)"""


def build_prompt(state: dict, memory: list[dict], inv: dict[str, int] | None = None) -> str:
    """Build the full LLM prompt from current game state and recent memory.

    Args:
        state:  Raw game state dict from game_state.json.
        memory: Recent memory entries from AgentMemory.
        inv:    Pre-parsed inventory counts (avoids re-parsing if caller already has it).
    """

    # Recent memory — prefer inventory/event entries first, then llm_reason
    memory_context = ""
    if memory:
        memory_context = "Recent events:\n"
        for entry in memory[-8:]:
            memory_context += f"  - [{entry.get('source', 'event')}] {entry['text']}\n"

    # Threat summary
    threat_summary = ""
    if state.get("threats"):
        threat_summary = (
            f"⚠️ THREATS NEARBY: {', '.join(t['name'] for t in state['threats'])}\n"
        )

    # Critical stat warnings
    def stat_label(value, max_value):
        try:
            v = float(value)
            return f"{v:.0f}/{max_value} {'[CRITICAL]' if v < CRITICAL_THRESHOLD else '[OK]'}"
        except (TypeError, ValueError):
            return f"{value}/{max_value}"

    # Inventory — truncate if too long
    inv = inv if inv is not None else _parse_inv(state)
    inventory_str = ", ".join(state.get("inventory", ["empty"]))
    if len(inventory_str) > 200:
        inventory_str = inventory_str[:197] + "..."

    prerequisites = _prerequisites_section(inv)

    # Nearby entities (top 5)
    nearby_lines = "\n".join(
        f"  • {e['name']} ({e['type']}) - {e['distance']}m away"
        for e in state.get("nearby_entities", [])[:5]
    )
    nearby_header = (
        "NEARBY ENTITIES:" if state.get("nearby_entities") else "No nearby entities"
    )

    action_list = ", ".join(ACTION_SPACE)

    return f"""{SYSTEM_RULES}

CURRENT STATUS:
- Day: {state.get("day", "?")}, Time: {state.get("time_of_day", 0):.2f} (0.75+ = dusk/night)
- Season: {state.get("season", "unknown")}
- Health: {stat_label(state.get("health"), 100)}
- Hunger: {stat_label(state.get("hunger"), 150)}
- Sanity: {stat_label(state.get("sanity"), 200)}
- Position: ({state.get("position", {}).get("x", "?")}, {state.get("position", {}).get("z", "?")})
- Equipped: {state.get("equipped", "nothing")}
- Inventory: {inventory_str}

{nearby_header}
{nearby_lines}

TOOLS & PREREQUISITES:
{prerequisites}

{threat_summary}
{memory_context}
Your action options: {action_list}

IMPORTANT: Respond ONLY with valid JSON in this format:
{{
  "action": "action_name",
  "reason": "Why you chose this action"
}}

Do NOT include any text outside the JSON."""
