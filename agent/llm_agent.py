#!/usr/bin/env python3
"""
llm_agent.py — Orchestrator. Coordinates collaborators to produce one action per tick.

All I/O, HTTP, parsing, and memory concerns are delegated to injected collaborators
(see main.py for wiring). This class only contains the decision loop.
"""

import random
import time

from action_parser import ActionParser
from action_writer import ActionWriter
from conversation_log import ConversationLog
from goal_manager import GoalManager, StateFieldError, _require_field, Urgency
from action_planner import (
    ActionPlanner as GoalPlanner,
)  # TODO GoalPlanner alias kept for attribute names
from inventory_tracker import InventoryTracker
from memory import AgentMemory
from models import ActionOption
from ollama_client import OllamaClient
from prompt import build_prompt
from state_reader import StateReader
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
        self._last_action: str | None = None
        self._last_action_changed: bool | None = (
            None  # did state change after last action?
        )

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
        """Read game state, apply emergency overrides, call LLM, write action."""
        state = self.state_reader.read()
        if not state:
            print("[Agent] Cannot read game state, exploring...")
            return self._emit(self._random_explore_action("No game state available"))

        if not self.state_reader.has_changed(state):
            print("[Agent] State unchanged, skipping decision")
            if self._last_action:
                self._last_action_changed = False
            return None

        self._last_action_changed = True if self._last_action else None

        if self.state_reader.is_game_over(state):
            self.memory.clear()
            self.memory.add("You died. Cleared stale memory.", "system")
            self.inventory_tracker.reset()
            self.world_tracker.reset()
            return self._emit(
                self._random_explore_action("Game over — waiting for new world")
            )

        if state.get("health", 0) <= 0:
            print("[Agent] You died — waiting for new world")
            return None

        if self.state_reader.is_world_reset(state):
            self.memory.clear()
            self.memory.add("World reset! Starting fresh.", "system")
            self.inventory_tracker.reset()
            self.world_tracker.reset()

        # Track what changed in inventory and world since last tick
        self.inventory_tracker.update(state)
        self.world_tracker.update(state)

        # Inventory snapshot used by override + planner
        inv = self.inventory_tracker.current

        # Emergency fast-path overrides (no LLM call needed)
        # Also validates required state fields via GoalManager — raises StateFieldError
        # if the Lua exporter is broken, which is caught below.
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

        # Compute concrete, specific actions from inventory + live state
        # Returns list of ActionOption objects with action/target/reason fields.
        # PrereqFilter already excludes blocked and redundant actions.
        concrete_actions = self.goal_planner.get_concrete_actions(inv, state)

        # Derive goals; preferred_actions bubble relevant variants to the top
        try:
            stg = self.goal_manager.get_short_term_goal(state, inv)
            goals = self.goal_manager.format_for_prompt(state, inv)
        except StateFieldError as exc:
            print(f"\n{'!' * 60}")
            print(str(exc))
            print("[Agent] Emitting random explore. Fix the Lua exporter then resume.")
            print(f"{'!' * 60}\n")
            return self._emit(self._random_explore_action("STATE BROKEN — PAUSE GAME"))

        # Bubble preferred actions to the top of the concrete list
        if stg and stg.preferred_actions:
            # A preferred prefix matches if the action name matches
            def _is_preferred(opt: ActionOption) -> bool:
                return any(opt.action == p.split(":")[0] for p in stg.preferred_actions)

            preferred = [a for a in concrete_actions if _is_preferred(a)]
            rest = [a for a in concrete_actions if not _is_preferred(a)]
            ordered: list[ActionOption] = preferred + rest
        else:
            ordered: list[ActionOption] = concrete_actions

        # Normal path: ask the LLM
        prompt = build_prompt(
            state,
            self.memory.recent(),
            inv,
            last_action=self._last_action,
            last_action_changed=self._last_action_changed,
            world_history=self.world_tracker.summary_lines(state),
            valid_actions=ordered,
            goals=goals,
        )
        raw = self.llm_client.generate(prompt)
        action = self.action_parser.parse(raw)

        # Validate: check if the LLM's action+target exists in our offered list
        # Build lookup: action name -> list of ActionOption objects
        actions_by_name: dict[str, list[ActionOption]] = {}
        for opt in ordered:
            actions_by_name.setdefault(opt.action, []).append(opt)

        chosen_action = action["action"]
        chosen_target = action.get("target")

        # Check if action name is valid
        if chosen_action not in actions_by_name:
            print(
                f"[Agent] INVALID: '{chosen_action}' not in valid_actions — forcing random explore"
            )
            self.memory.add(
                f"Rejected '{chosen_action}' (not in valid actions), forced explore",
                "system",
            )
            action = self._random_explore_action(f"'{chosen_action}' not a valid action")
        elif chosen_action in actions_by_name:
            # Validate target if needed
            valid_opts = actions_by_name[chosen_action]
            needs_target = any(opt.target is not None for opt in valid_opts)
            
            if needs_target and not chosen_target:
                print(
                    f"[Agent] INVALID: '{chosen_action}' missing required target — forcing random explore"
                )
                self.memory.add(
                    f"Rejected '{chosen_action}' (missing target), forced explore",
                    "system",
                )
                action = self._random_explore_action(
                    f"'{chosen_action}' must include a specific target"
                )

        self.conversation_log.record(prompt, raw or "", action)

        self.memory.add(action["reason"], "llm_reason")

        self.decision_count += 1
        return self._emit(action)

    def run(self, interval: float = 5.0) -> None:
        """Poll decide() every interval seconds until interrupted."""
        print(
            f"[DSAIAgent] Starting — model={self.llm_client.model}, interval={interval}s"
        )
        print("[DSAIAgent] Press Ctrl+C to stop\n")
        try:
            while True:
                self.decide()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n[DSAIAgent] Stopped after {self.decision_count} decisions.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _emergency_override(self, state: dict, inv: dict[str, int]) -> dict | None:
        """Return a hardcoded action for critical situations, or None.

        Raises StateFieldError if required vitals are missing in the state.
        Callers must catch this and emit explore + warn.
        """
        health = _require_field(state, "health", float)
        threats = state.get("threats") or []  # None → no threats (safe)
        time_of_day = state.get("time_of_day") or 0.0  # None → assume daytime (safe)

        if health < 20:
            print("[Agent] CRITICAL: Health very low!")
            return {"action": "eat_food", "reason": "Health critically low"}

        if threats:
            t = threats[0]
            print(f"[Agent] WARNING: {t['name']} nearby!")
            return {
                "action": "run_from_enemy",
                "reason": f"Hostile {t['name']} at {t['distance']}m",
            }

        if time_of_day > 0.75:
            stg = self.goal_manager.get_short_term_goal(state, inv)
            if stg and stg.urgency in (Urgency.CRITICAL, Urgency.URGENT):
                # Pick the first preferred action that's actually craftable
                valid_set = set(self.goal_planner.get_valid_actions(inv))
                for act in stg.preferred_actions:
                    if act in valid_set:
                        print(f"[Agent] DUSK/NIGHT: {stg.description[:60]}")
                        return {"action": act, "reason": stg.description}
                # Nothing craftable yet — gather materials
                print("[Agent] DUSK/NIGHT: Need fire materials, gathering resource")
                return {"action": "gather_resource", "reason": stg.description}

        return None

    def _emit(self, action: dict) -> dict:
        self._last_action = action["action"]
        self.action_writer.write(action)
        return action
