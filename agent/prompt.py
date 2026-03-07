"""
prompt.py — Builds the LLM prompt from game state and memory.

Keeping prompt logic separate makes it easy to tune instructions
without touching agent plumbing.
"""

from models import GameState

# Available actions surfaced to the LLM
ACTION_SPACE = [
    "move_to_food",
    "chop_tree",
    "mine_rock",
    "pick_up_item",
    "craft_item",
    "eat_food",
    "cook_food",
    "run_from_enemy",
    "attack_enemy",
    "explore",
]

CRITICAL_THRESHOLD = 50  # Health/hunger/sanity below this = urgent action required

# Crafting recipes: item -> {ingredient: count}
RECIPES: dict[str, dict[str, int]] = {
    "axe": {"twig": 1, "flint": 1},
    "pickaxe": {"twig": 2, "flint": 2},
    "campfire": {"log": 2, "cutgrass": 2},
    "torch": {"twig": 2, "cutgrass": 2},
}


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
Use the exact action name and target from the list.
If your goal requires something not currently available (e.g. flint not nearby), pick explore — do NOT idle.
"""


def build_prompt(
    state: GameState,
    memory: list[dict],
    inv: dict[str, int] | None = None,
    last_action: str | None = None,
    last_action_changed: bool | None = None,
    world_history: str = "",
    valid_actions: list | None = None,
    goals: str = "",
) -> str:
    """Build the full LLM prompt from current game state and recent memory.

    Args:
        state:               GameState model instance.
        memory:              Recent memory entries from AgentMemory.
        inv:                 Pre-parsed inventory counts (optional, computed from state if not provided).
        last_action:         Action chosen on the previous tick.
        last_action_changed: True if state changed after it, False if not, None if unknown.
        world_history:       Compact string of recently-seen-but-gone entities.
        valid_actions:       List of ActionOption objects (pre-filtered).
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
    if state.threats:
        threat_lines += "[WARN]"
        threat_lines = "\n".join(
            f"  {t.name} at {t.distance}m" for t in state.threats
        )
        threat_lines += "[/WARN]"

    # Critical stat warnings
    def stat_label(value, max_value):
        try:
            v = float(value)
            return f"{v:.0f}/{max_value} {'[CRITICAL]' if v < CRITICAL_THRESHOLD else '[OK]'}"
        except (TypeError, ValueError):
            return f"{value}/{max_value}"

    # Inventory — compact single line using parsed counts
    inv = inv if inv is not None else state.get_inventory_dict()
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
            f"  - {e.name} ({e.type}) - {e.distance}m"
            for e in state.nearby_entities[:5]
        )
        or "  (none)"
    )

    # Wilson's speech + action results since last export (buffered lists)
    feedback_lines = ""
    for s in state.speech_log:
        feedback_lines += f'  Wilson said: "{s}"\n'
    for a in state.action_log:
        if a.result == "failed":
            feedback_lines += f"  Action failed: {a.action} — {a.reason or '?'}\n"
        else:
            feedback_lines += f"  Action ok: {a.action}\n"

    # Current in-progress action (bufferedaction from behavior tree)
    current_action_line = ""
    if state.current_action:
        current_action_line = (
            f"  Doing: {state.current_action}"
            + (f" -> {state.action_target}" if state.action_target else "")
            + "\n"
        )

    # Weather
    rain_str = " RAINING" if state.is_raining else ""
    temp_str = f" Temp:{state.temperature}C" if state.temperature is not None else ""

    # Format valid actions list - group by action type
    from collections import defaultdict

    valid_actions = valid_actions or []
    if valid_actions:
        # Group actions by action name
        grouped: dict[str, list[str | None]] = defaultdict(list)
        for opt in valid_actions:
            grouped[opt.action].append(opt.target)

        # Format grouped actions - skip actions with no valid targets
        action_lines = []
        for action_name, targets in grouped.items():
            # Filter out None targets and keep unique targets
            valid_targets = [t for t in targets if t is not None]
            if len(valid_targets) == 0:
                # Skip actions without targets
                continue
            elif len(valid_targets) == 1:
                # Single target - use singular format
                action_lines.append(
                    f'  {{"action":"{action_name}", "target":"{valid_targets[0]}"}}'
                )
            else:
                # Multiple targets - use array format
                targets_str = ", ".join(f'"{t}"' for t in valid_targets)
                action_lines.append(
                    f'  {{"action":"{action_name}", "targets":[{targets_str}]}}'
                )

        actions_text = "\n".join(action_lines)
    else:
        actions_text = (
            '  {"action":"explore", "targets":["N","S","E","W","NE","NW","SE","SW"]}'
        )

    return f"""{SYSTEM_RULES}
{"[GOALS]" + chr(10) + "  " + goals + chr(10) + "[/GOALS]" + chr(10) if goals else ""}
[STATUS]
  Day:{state.day} Phase:{state.phase} Season:{state.season}{rain_str}{temp_str}
  Health:{stat_label(state.health, 100)} Hunger:{stat_label(state.hunger, 150)} Sanity:{stat_label(state.sanity, 200)}
  Equipped:{state.equipped or "none"}
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

YOUR ONLY VALID CHOICES — pick exactly one action+target combination:
[VALID_ACTIONS]
{actions_text}
[/VALID_ACTIONS]

Reply ONLY with JSON — no extra text, no markdown, no explanation.
Each action shows "targets": [...]. Pick ONE value from the targets array.
Format: {{"action":"action_name","target":"chosen_target","reason":"why"}}"""
