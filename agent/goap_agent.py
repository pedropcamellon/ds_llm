#!/usr/bin/env python3
"""
llm_agent.py — GOAP-based agent with strategic LLM planning.

Architecture:
  - LLM called on phase changes (4x per day max) for strategic goal selection
  - GOAP executor handles per-tick tactical actions toward the goal
  - Emergency overrides for threats/health/fire (no LLM, no GOAP)

All I/O, HTTP, parsing, and memory concerns are delegated to injected collaborators.
"""

import json
import random
import re
import time

from action_parser import ActionParser
from action_writer import ActionWriter
from conversation_log import ConversationLog
from goal_manager import GoalManager, Urgency
from action_planner import (
    ActionPlanner as GoalPlanner,
)  # TODO GoalPlanner alias kept for attribute names
from goap_executor import get_next_action_for_goal, is_goal_satisfied
from inventory_tracker import InventoryTracker
from memory import AgentMemory
from models import ActionOption, GameState
from ollama_client import OllamaClient
from state_reader import StateReader
from state_manager import StateFieldError, require_field
from strategic_goals import STRATEGIC_GOALS, get_suggested_goals
from strategic_prompt import build_strategic_prompt
from world_tracker import WorldTracker

# Available exploration directions for fallback actions
_EXPLORE_DIRECTIONS = ["N", "S", "E", "W", "NE", "NW", "SE", "SW"]


class DSAIAgent:
    def __init__(
        self,
        state_reader: StateReader,
        memory: AgentMemory,
        llm_client: OllamaClient,
        action_parser: ActionParser,
        action_writer: ActionWriter,
        inventory_tracker: InventoryTracker,
        conversation_log: ConversationLog,
        world_tracker: WorldTracker,
        goal_planner: GoalPlanner,
        goal_manager: GoalManager,
    ):
        self.state_reader = state_reader
        self.memory = memory
        self.llm_client = llm_client
        self.action_parser = action_parser
        self.action_writer = action_writer
        self.inventory_tracker = inventory_tracker
        self.conversation_log = conversation_log
        self.world_tracker = world_tracker
        self.goal_planner = goal_planner
        self.goal_manager = goal_manager
        self.decision_count = 0
        self.llm_call_count = 0
        self.goap_action_count = 0
        # GOAP state
        self._current_goal: str | None = None
        self._last_phase: str = ""
        self._last_action: str | None = None
        self._last_action_changed: bool | None = None

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------

    @staticmethod
    def _random_explore_action(reason: str) -> dict:
        """Return explore action with random direction to avoid directional bias.

        TODO: Future improvements for exploration strategy:
        - Track previously explored directions and prefer unexplored ones
        - Avoid immediate backtracking (opposite direction of last explore)
        - Use cartographer data to prefer directions with unexplored map tiles
        - Weight directions based on nearby entities (resources, threats)
        """
        return {
            "action": "explore",
            "target": random.choice(_EXPLORE_DIRECTIONS),
            "reason": reason,
        }

    def decide(self) -> dict | None:
        """Main decision loop — dispatches to LLM or GOAP based on context."""
        state = self.state_reader.read()
        if not state:
            print("[Agent] Cannot read game state, exploring...")
            return self._emit(self._random_explore_action("No game state available"))

        # Skip if state unchanged
        if not self.state_reader.has_changed(state):
            return None

        # Handle resets
        if self.state_reader.is_world_reset(state):
            self._current_goal = None
            self.memory.clear()
            self.memory.add("World reset! Starting fresh.", "system")
            self.inventory_tracker.reset()
            self.world_tracker.reset()

        if self.state_reader.is_game_over(state):
            self._current_goal = None
            self.memory.clear()
            self.memory.add("You died. Cleared stale memory.", "system")
            self.inventory_tracker.reset()
            self.world_tracker.reset()
            return self._emit(self._random_explore_action("Game over — waiting"))

        # Update trackers
        self.inventory_tracker.update(state)
        self.world_tracker.update(state)
        inv = self.inventory_tracker.current

        # Emergency overrides (no LLM, no GOAP — immediate response)
        try:
            override = self._emergency_override(state, inv)
        except StateFieldError as exc:
            print(f"\n{'!' * 60}")
            print(str(exc))
            print("[Agent] Emitting random explore. Fix the Lua exporter then resume.")
            print(f"{'!' * 60}\n")
            return self._emit(self._random_explore_action("STATE BROKEN — PAUSE GAME"))
        if override:
            return self._emit(override)

        # Check if we should call LLM (phase change or no goal)
        should_call, reason = self.state_reader.should_call_llm(state)
        phase_changed = "phase_change" in reason

        if should_call or self._current_goal is None:
            return self._strategic_decide(state, inv, phase_changed)
        else:
            return self._goap_decide(state, inv)

    def _strategic_decide(
        self, state: GameState, inv: dict[str, int], phase_changed: bool
    ) -> dict | None:
        """Call LLM for strategic goal selection."""
        self.llm_call_count += 1

        # Build phase transition string
        current_phase = state.phase.lower()
        if phase_changed and self._last_phase:
            transition = f"{self._last_phase} → {current_phase}"
        else:
            transition = f"start of {current_phase}"
        self._last_phase = current_phase

        # Get suggested goals for display
        threats_nearby = bool(state.threats)
        suggested = get_suggested_goals(
            phase=state.phase,
            health=state.health,
            hunger=state.hunger,
            inv=inv,
            threats_nearby=threats_nearby,
        )
        suggested_names = [g.name for g in suggested]

        print(f"\n{'=' * 60}")
        print(f"[STRATEGIC] Phase: {transition}")
        print(f"[STRATEGIC] Suggested goals: {', '.join(suggested_names)}")

        # Get memory summary
        recent_memory = self.memory.recent(max_entries=3)
        memory_lines = [m.get("text", "") for m in recent_memory]
        memory_summary = " | ".join(memory_lines) if memory_lines else ""

        # Build strategic prompt
        prompt = build_strategic_prompt(
            state=state,
            inv=inv,
            phase_transition=transition,
            memory_summary=memory_summary,
        )

        print(f"[STRATEGIC] LLM call #{self.llm_call_count}...")

        # Call LLM with error handling
        raw = None
        try:
            raw = self.llm_client.generate(prompt)
        except Exception as e:
            print(f"[STRATEGIC] LLM error: {e}")
            print("[STRATEGIC] Falling back to heuristic goal selection")
            self._current_goal = self._fallback_goal(state, inv)
            print(f"[STRATEGIC] Fallback goal: {self._current_goal}")
            self.memory.add(f"LLM unavailable, using {self._current_goal}", "system")
            return self._goap_decide(state, inv)

        goal_response = self._parse_goal_response(raw)

        if goal_response and goal_response.get("goal") in STRATEGIC_GOALS:
            self._current_goal = goal_response["goal"]
            reason = goal_response.get("reason", "")
            print(f"[STRATEGIC] LLM chose: {self._current_goal}")
            print(f"[STRATEGIC] Reason: {reason}")
            self.memory.add(f"Goal: {self._current_goal} ({reason})", "strategic")
        else:
            # Fallback to heuristic
            self._current_goal = self._fallback_goal(state, inv)
            print(f"[STRATEGIC] Invalid LLM response, fallback: {self._current_goal}")

        self.conversation_log.record(prompt, raw or "", {"goal": self._current_goal})

        # Now execute first GOAP step toward the goal
        return self._goap_decide(state, inv)

    def _goap_decide(self, state: GameState, inv: dict[str, int]) -> dict | None:
        """Use GOAP to compute next action toward current goal."""
        self.goap_action_count += 1

        if not self._current_goal:
            self._current_goal = "gather_basics"

        # Check if goal is satisfied
        if is_goal_satisfied(self._current_goal, state, inv):
            print(f"[GOAP] Goal '{self._current_goal}' SATISFIED!")
            self.memory.add(f"Completed: {self._current_goal}", "achievement")
            # Will get new goal on next phase change
            self._current_goal = "explore_area"

        # Get nearby items for GOAP planning
        nearby = [e.name for e in (state.nearby_entities or []) if e.name]

        # Compute next action
        plan = get_next_action_for_goal(self._current_goal, state, inv, nearby)

        # Show GOAP chain
        print(f"\n[GOAP] Goal: {self._current_goal}")
        if plan.steps:
            print(f"[GOAP] Plan: {' → '.join(plan.steps)}")
        else:
            print(f"[GOAP] No plan steps computed")

        if plan.next_action:
            action = {
                "action": plan.next_action.action,
                "target": plan.next_action.target,
                "reason": plan.next_action.reason,
            }
            print(f"[GOAP] → Action: {action['action']} target={action['target']}")
            print(f"[GOAP]   Reason: {action['reason']}")
            print(f"{'=' * 60}")
            self._last_action = f"{action['action']}:{action['target']}"
            return self._emit(action)
        else:
            print(f"[GOAP] Blocked: {plan.blocked_reason}")
            print(f"[GOAP] → Fallback: explore random direction")
            print(f"{'=' * 60}")
            return self._emit(
                self._random_explore_action(plan.blocked_reason or "blocked")
            )

    def _parse_goal_response(self, raw: str | None) -> dict | None:
        """Parse LLM response for goal selection."""
        if not raw:
            return None
        try:
            # Try to extract JSON from response
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to find JSON in response
            match = re.search(r"\{[^}]+\}", raw)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _emergency_override(self, state: GameState, inv: dict[str, int]) -> dict | None:
        """Return a hardcoded action for critical situations, or None.

        Raises StateFieldError if required vitals are missing in the state.
        Callers must catch this and emit explore + warn.
        """
        health = require_field(state, "health", float)
        threats = state.threats or []  # None → no threats (safe)
        phase = (state.phase or "day").lower()

        if health < 20:
            print("[Agent] CRITICAL: Health very low!")
            # Try to eat something
            for item in inv:
                if any(food in item.lower() for food in ("berries", "carrot", "meat")):
                    return {
                        "action": "eat_food",
                        "target": item,
                        "reason": "Health critical",
                    }
            return {
                "action": "run_from_enemy",
                "target": "away",
                "reason": "Health critical, no food",
            }

        if threats:
            t = threats[0]
            tname = (t.name or "unknown").lower()
            tdist = t.distance or "?"
            print(f"[Agent] WARNING: {tname} nearby!")
            return {
                "action": "run_from_enemy",
                "target": "away",
                "reason": f"Fleeing from {tname} at {tdist}m",
            }

        # Night with no light
        if phase == "night":
            has_light = inv.get("torch", 0) > 0 or any(
                e.name in ("campfire", "firepit", "torch")
                for e in (state.nearby_entities or [])
            )
            if not has_light:
                # Can we craft torch?
                if inv.get("twigs", 0) >= 2 and inv.get("cutgrass", 0) >= 2:
                    print("[Agent] CRITICAL: Night! Crafting torch")
                    return {
                        "action": "craft_item",
                        "target": "torch",
                        "reason": "Night without light",
                    }
                print("[Agent] CRITICAL: Night without light")
                return {
                    "action": "explore",
                    "target": random.choice(_EXPLORE_DIRECTIONS),
                    "reason": "Night! Looking for fire",
                }

        return None

    def _fallback_goal(self, state: GameState, inv: dict[str, int]) -> str:
        """Heuristic goal selection when LLM is unavailable."""
        phase = (state.phase or "day").lower()

        # Priority-based fallback
        if phase in ("dusk", "night"):
            has_light = inv.get("torch", 0) > 0
            if not has_light:
                return "prepare_light"

        if state.hunger < 50:
            return "find_food"

        if state.health < 50:
            return "heal_up"

        # Check for basic materials
        if inv.get("cutgrass", 0) < 3 or inv.get("twigs", 0) < 3:
            return "gather_basics"

        # Check for tools
        if inv.get("axe", 0) == 0 and inv.get("flint", 0) >= 1:
            return "craft_tools"

        return "gather_basics"

    def _emit(self, action: dict) -> dict:
        """Write action and return it."""
        self.action_writer.write(action)
        self.decision_count += 1
        return action

    def test_once(self, state: GameState, force_llm: bool = False) -> dict:
        """Run one decision cycle for testing. Returns action + metadata."""
        # Update trackers with provided state
        self.inventory_tracker.update(state)
        self.world_tracker.update(state)
        inv = self.inventory_tracker.current

        # Get nearby items
        nearby = [e.name for e in (state.nearby_entities or []) if e.name]

        # Check emergency first
        try:
            override = self._emergency_override(state, inv)
        except StateFieldError as exc:
            return {
                "action": "explore",
                "target": "N",
                "reason": str(exc),
                "_meta": {"error": str(exc)},
            }

        if override:
            return {**override, "_meta": {"layer": "emergency"}}

        # Determine goal
        if force_llm:
            # Force LLM call
            action = self._strategic_decide(state, inv, phase_changed=True)
        else:
            # Use heuristic goal selection (no LLM)
            self._current_goal = self._fallback_goal(state, inv)
            action = self._goap_decide(state, inv)

        # Get GOAP plan for visibility
        goal = self._current_goal or "gather_basics"
        plan = get_next_action_for_goal(goal, state, inv, nearby)

        if action:
            action["_meta"] = {
                "goal": goal,
                "goap_steps": plan.steps if plan else [],
                "llm_called": force_llm,
            }

        return action or {"action": "idle", "reason": "no action", "_meta": {}}

    def run(self, interval: float = 5.0) -> None:
        """Poll decide() every interval seconds."""
        print(f"[DSAIAgent] Starting — model={self.llm_client.model}")
        print(f"[DSAIAgent] GOAP mode: LLM on phase changes, GOAP per-tick")
        print("[DSAIAgent] Press Ctrl+C to stop\n")
        try:
            while True:
                self.decide()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n[DSAIAgent] Stopped.")
            print(f"  Decisions: {self.decision_count}")
            print(f"  LLM calls: {self.llm_call_count}")
            print(f"  GOAP actions: {self.goap_action_count}")
