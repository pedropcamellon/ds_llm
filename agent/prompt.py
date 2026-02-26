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

SYSTEM_RULES = """You are Wilson in Don't Starve. You must survive by gathering resources, cooking food, and managing your health.

CRITICAL RULES:
- DARKNESS KILLS YOU. Always have a fire before night or you die.
- Stats below 50 are CRITICAL and require immediate action. Stats above 50 are safe — do not waste food or resources.
- Hunger max is 150. Only eat if hunger < 50. Eating at 119/150 is wasteful.
- Health max is 100. Only heal if health < 50.
- Sanity max is 200. Only address sanity if sanity < 50.
- Build tools (axe, pickaxe) to gather resources efficiently.
- Seasons change: autumn (safe) → winter (cold, scarce food) → spring (rain) → summer (heat)"""


def build_prompt(state: dict, memory: list[dict]) -> str:
    """Build the full LLM prompt from current game state and recent memory."""

    # Recent memory (last 5 entries)
    memory_context = ""
    if memory:
        memory_context = "Recent events:\n"
        for entry in memory[-5:]:
            memory_context += f"  - {entry['text']}\n"

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
    inventory_str = ", ".join(state.get("inventory", ["empty"]))
    if len(inventory_str) > 200:
        inventory_str = inventory_str[:197] + "..."

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

{threat_summary}
{memory_context}
Your action options: {action_list}

IMPORTANT: Respond ONLY with valid JSON in this format:
{{
  "action": "action_name",
  "reason": "Why you chose this action"
}}

Do NOT include any text outside the JSON."""
