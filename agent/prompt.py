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


SYSTEM_RULES = """Survive in the wild. Survive as long as possible.
Always act on the SHORT-TERM GOAL first. If no urgent goal, work toward the LONG-TERM GOAL.
YOU MUST pick from VALID_ACTIONS (listed at the bottom). Never invent an action.
Actions with a colon REQUIRE the full name including the target (e.g. pick_up_item:twigs, gather_resource:log).
Writing just "pick_up_item" when the list shows "pick_up_item:twigs" is WRONG — you must copy the FULL string.
If your goal requires something not currently available (e.g. flint not nearby), pick explore — do NOT idle.
"""


def build_prompt(
    state: dict,
    memory: list[dict],
    inv: dict[str, int] | None = None,
    last_action: str | None = None,
    last_action_changed: bool | None = None,
    world_history: str = "",
    valid_actions: str = "",
    goals: str = "",
) -> str:
    """Build the full LLM prompt from current game state and recent memory.

    Args:
        state:               Raw game state dict from game_state.json.
        memory:              Recent memory entries from AgentMemory.
        inv:                 Pre-parsed inventory counts.
        last_action:         Action chosen on the previous tick.
        last_action_changed: True if state changed after it, False if not, None if unknown.
        world_history:       Compact string of recently-seen-but-gone entities.
        valid_actions:       Pre-filtered action list (blocked + redundant already removed).
        goals:               Formatted goals block from GoalManager.
    """

    # Last-action feedback
    last_action_line = ""
    if last_action:
        if last_action_changed is False:
            last_action_line = f"[LAST_ACTION]{chr(10)}  {last_action} -> no state change (action had no effect){chr(10)}[/LAST_ACTION]{chr(10)}{chr(10)}"
        elif last_action_changed is True:
            last_action_line = f"[LAST_ACTION]{chr(10)}  {last_action} -> state changed{chr(10)}[/LAST_ACTION]{chr(10)}{chr(10)}"

    # Recent memory — show up to 8 entries, but collapse consecutive duplicate
    # llm_reason entries into one so the model doesn't get anchored to a
    # stale reasoning loop (e.g. "I need flint" repeated 6 times in a row).
    memory_lines = ""
    if memory:
        filtered: list[dict] = []
        last_llm_reason: str | None = None
        for entry in memory[-12:]:  # look at more, show at most 8
            if entry.get("source") == "llm_reason":
                if entry["text"] == last_llm_reason:
                    continue  # skip duplicate
                last_llm_reason = entry["text"]
            filtered.append(entry)
        for entry in filtered[-8:]:
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
            f"  - {e['name']} ({e['type']}) - {e['distance']}m"
            for e in state.get("nearby_entities", [])[:5]
        )
        or "  (none)"
    )

    # Wilson's speech + action results since last export (buffered lists)
    speech_log = state.get("speech_log") or []
    action_log = state.get("action_log") or []
    feedback_lines = ""
    for s in speech_log:
        feedback_lines += f'  Wilson said: "{s}"\n'
    for a in action_log:
        if a.get("result") == "failed":
            feedback_lines += (
                f"  Action failed: {a.get('action')} — {a.get('reason', '?')}\n"
            )
        else:
            feedback_lines += f"  Action ok: {a.get('action')}\n"

    # Current in-progress action (bufferedaction from behavior tree)
    cur_action = state.get("current_action")
    cur_target = state.get("action_target")
    current_action_line = ""
    if cur_action:
        current_action_line = (
            f"  Doing:{cur_action}" + (f" -> {cur_target}" if cur_target else "") + "\n"
        )

    # Weather
    rain_str = " RAINING" if state.get("is_raining") else ""
    temp = state.get("temperature")
    temp_str = f" Temp:{temp}C" if temp is not None else ""

    return f"""{SYSTEM_RULES}
{"[GOALS]" + chr(10) + "  " + goals + chr(10) + "[/GOALS]" + chr(10) if goals else ""}
[STATUS]
  Day:{state.get("day", "?")} Phase:{state.get("phase", "?")} Season:{state.get("season", "?")}{rain_str}{temp_str}
  Health:{stat_label(state.get("health"), 100)} Hunger:{stat_label(state.get("hunger"), 150)} Sanity:{stat_label(state.get("sanity"), 200)}
  Equipped:{state.get("equipped", "none")}
{current_action_line}[/STATUS]

[INVENTORY]
  {inv_line}
[/INVENTORY]

[NEARBY]
{nearby_lines}
[/NEARBY]
{"[WORLD_HISTORY]" + chr(10) + "  Recently seen (now out of view): " + world_history + chr(10) + "[/WORLD_HISTORY]" + chr(10) if world_history else ""}
[TOOLS]
{prerequisites}
[/TOOLS]

{last_action_line}{"[FEEDBACK]" + chr(10) + feedback_lines.rstrip() + chr(10) + "[/FEEDBACK]" + chr(10) if feedback_lines else ""}{"[THREATS]" + chr(10) + threat_lines + chr(10) + "[/THREATS]" + chr(10) if threat_lines else ""}[MEMORY]
{memory_lines.rstrip() or "  (none)"}
[/MEMORY]

YOUR ONLY VALID CHOICES — pick exactly one, copy name verbatim:
[VALID_ACTIONS]
  {valid_actions or "explore\n  idle"}
[/VALID_ACTIONS]

Reply ONLY with JSON — no extra text, no markdown, no explanation:
{{"action":"exact_action_from_list_above","reason":"why"}}"""
