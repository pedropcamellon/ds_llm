"""
debug_cli.py — Offline debug tool for testing game state processing.

Loads a game_state.json snapshot, runs the full pipeline (parsing, goals,
action planning, prompt building), and displays results without running the
game or calling Ollama (unless --with-llm is specified).
"""

import argparse
import json
import sys
from pathlib import Path

from action_parser import ActionParser
from action_planner import ActionPlanner
from goal_manager import GoalManager
from inventory_tracker import InventoryTracker
from memory import AgentMemory
from ollama_client import OllamaClient
from prompt import build_prompt
from world_tracker import WorldTracker


def main():
    parser = argparse.ArgumentParser(
        description="Debug tool: load game state and show decision pipeline"
    )
    parser.add_argument("state_file", type=Path, help="Path to game_state.json")
    parser.add_argument(
        "--actions-only", action="store_true", help="Show only action lists"
    )
    parser.add_argument(
        "--prompt-only", action="store_true", help="Show only the LLM prompt"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as machine-readable JSON"
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="Actually call Ollama and show response",
    )
    parser.add_argument(
        "--model", default="llama3.2:latest", help="Ollama model to use (if --with-llm)"
    )
    args = parser.parse_args()

    # Load state
    if not args.state_file.exists():
        print(f"Error: {args.state_file} not found", file=sys.stderr)
        return 1

    with open(args.state_file) as f:
        state = json.load(f)

    # Instantiate modules
    inv_tracker = InventoryTracker(AgentMemory(Path("_debug_memory.jsonl")))
    inv = inv_tracker.update(state)

    world_tracker = WorldTracker(ttl_seconds=120.0)
    world_tracker.update(state)

    goal_manager = GoalManager()
    goals_text = goal_manager.format_for_prompt(state, inv)
    stg = goal_manager.get_short_term_goal(state, inv)

    planner = ActionPlanner()
    concrete_actions = planner.get_concrete_actions(inv, state)

    # Build prompt
    prompt_text = build_prompt(
        state,
        memory=[],  # no memory for single-shot debug
        inv=inv,
        valid_actions=concrete_actions,
        goals=goals_text,
        world_history=world_tracker.summary_lines(state),
    )

    # Convert actions to display format for JSON output
    actions_display = [
        {"action": opt.action, "target": opt.target, "reason": opt.reason}
        for opt in concrete_actions
    ]

    # Group actions by action name for formatted display
    from collections import defaultdict

    grouped_actions: dict[str, list[str | None]] = defaultdict(list)
    for opt in concrete_actions:
        grouped_actions[opt.action].append(opt.target)

    # Output formatting
    if args.json:
        output = {
            "state_summary": _state_summary(state),
            "goals": goals_text,
            "short_term_goal": stg.description if stg else None,
            "concrete_actions": actions_display,
            "prompt": prompt_text,
        }
        if args.with_llm:
            output["llm_response"] = _call_llm(prompt_text, args.model)
        print(json.dumps(output, indent=2))
    elif args.actions_only:
        print("[CONCRETE ACTIONS]")
        for action_name, targets in grouped_actions.items():
            valid_targets = [t for t in targets if t is not None]
            if len(valid_targets) == 0:
                # Skip actions without targets
                continue
            else:
                targets_str = ", ".join(f'"{t}"' for t in valid_targets)
                print(f'  {{"action": "{action_name}", "targets": [{targets_str}]}}')
    elif args.prompt_only:
        print(prompt_text)
    else:
        # Full output
        print("=" * 80)
        print("[STATE SUMMARY]")
        print(_state_summary(state))
        print("\n" + "=" * 80)
        print("[GOALS]")
        print(goals_text)
        if stg:
            print(f"\nShort-term goal: {stg.description} (urgency: {stg.urgency.name})")
        print("\n" + "=" * 80)
        print(f"[CONCRETE ACTIONS] ({len(concrete_actions)} available)")
        displayed = 0
        for action_name, targets in grouped_actions.items():
            if displayed >= 20:
                break
            valid_targets = [t for t in targets if t is not None]
            if len(valid_targets) == 0:
                # Skip actions without targets
                continue
            else:
                targets_str = ", ".join(f'"{t}"' for t in valid_targets)
                print(f'  {{"action": "{action_name}", "targets": [{targets_str}]}}')
            displayed += 1
        if len(concrete_actions) > 20:
            print(f"  ... and {len(concrete_actions) - 20} more")
        print("\n" + "=" * 80)
        print("[FULL PROMPT]")
        print(prompt_text)

        if args.with_llm:
            print("\n" + "=" * 80)
            print("[LLM RESPONSE]")
            response = _call_llm(prompt_text, args.model)
            print(response.get("raw", ""))
            print("\n[PARSED ACTION]")
            print(json.dumps(response.get("action", {}), indent=2))

    return 0


def _state_summary(state: dict) -> str:
    """Format a compact state summary."""
    return f"""Day {state.get("day", "?")}, {state.get("season", "?")}, {state.get("phase", "?")} (time: {state.get("time_of_day", 0):.2f})
Health: {state.get("health", "?")} | Hunger: {state.get("hunger", "?")} | Sanity: {state.get("sanity", "?")}
Temperature: {state.get("temperature", "?")}°C | Raining: {state.get("is_raining", False)}
Inventory: {", ".join(state.get("inventory", [])[:10])}
Equipped: {state.get("equipped", "none")}
Nearby entities: {len(state.get("nearby_entities", []))} | Threats: {len(state.get("threats", []))}"""


def _call_llm(prompt: str, model: str) -> dict:
    """Call Ollama and parse response."""
    client = OllamaClient(model=model)
    parser = ActionParser()

    try:
        raw_response = client.generate(prompt)
        action = parser.parse(raw_response)
        return {"raw": raw_response, "action": action}
    except Exception as e:
        return {"error": str(e), "raw": "", "action": {}}


if __name__ == "__main__":
    sys.exit(main())
