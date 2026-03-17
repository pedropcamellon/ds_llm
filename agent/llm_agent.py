#!/usr/bin/env python3
"""
llm_agent.py — Orchestrator. Coordinates collaborators to produce one action per tick.

All I/O, HTTP, parsing, and memory concerns are delegated to injected collaborators
(see main.py for wiring). This class only contains the decision loop.
"""

import logging
import random
import time

from action_parser import ActionParser
from action_writer import ActionWriter
from conversation_log import ConversationLog
from goal_manager import GoalManager, Urgency
from action_planner import (
    ActionPlanner as GoalPlanner,
)  # TODO GoalPlanner alias kept for attribute names
from goals.models import ActiveGoal
from inventory_tracker import InventoryTracker
from memory import AgentMemory
from models import GameState
from ollama_client import OllamaClient
from prompt import create_default_builder
from state_reader import StateReader
from state_manager import StateFieldError, require_field
from utils.parsing import parse_goal_choice
from world_tracker import WorldTracker

logger = logging.getLogger(__name__)

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
        self._current_mid_term_goal: ActiveGoal | None = (
            None  # Selected goal with metadata
        )
        self._goal_selection_interval = 5  # Select new goal every N decisions

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
            logger.warning("Cannot read game state, exploring randomly")
            return self._emit(self._random_explore_action("No game state available"))

        # TODO if not self.state_reader.has_changed(state):
        #     logger.debug("State unchanged, skipping decision")
        #     if self._last_action:
        #         self._last_action_changed = False
        #     return

        # self._last_action_changed = True if self._last_action else None

        if self.state_reader.is_game_over(state):
            logger.info("Game over - clearing memory and waiting for new world")
            self.memory.clear()
            self.memory.add("You died. Cleared stale memory.", "system")
            self.inventory_tracker.reset()
            self.world_tracker.reset()
            return self._emit(
                self._random_explore_action("Game over — waiting for new world")
            )

        if state.health <= 0:
            logger.info("Health depleted - waiting for respawn")
            return None

        if self.state_reader.is_world_reset(state):
            logger.info("World reset detected - clearing memory")
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
            logger.error(f"\n{'!' * 60}")

            logger.error(f"State validation failed: {exc}")
            logger.error("Fix Lua exporter then resume - emitting random explore")
            logger.error(f"{'!' * 60}\n")
            return self._emit(self._random_explore_action("STATE BROKEN — PAUSE GAME"))
        if override:
            logger.info(
                f"Emergency override: {override['action']} - {override['reason']}"
            )
            return self._emit(override)

        # Check goal completion (before selection logic)
        self._check_goal_completion(state)

        # Phase 1: Select mid-term goal (every N decisions or if no goal)
        if (
            self.decision_count % self._goal_selection_interval == 0
            or not self._current_mid_term_goal
        ):
            try:
                self._select_mid_term_goal(state, inv)
            except Exception as exc:
                logger.error(f"Mid-term goal selection failed: {exc}")
                logger.warning("Continuing with exploration")

        logger.info(f"Day {state.day} {state.phase}")
        logger.info(
            f"Current mid-term goal: {self._current_mid_term_goal.goal.description if self._current_mid_term_goal else 'None'}"
        )

        # ---- COMMENTED OUT: Phase 2 - Action Selection ----
        # TODO: Re-enable once Phase 1 (mid-term goal selection) is validated
        #
        # # Compute concrete, specific actions from inventory + live state
        # # Returns list of ActionOption objects with action/target/reason fields.
        # # PrereqFilter already excludes blocked and redundant actions.
        # concrete_actions = self.goal_planner.get_concrete_actions(inv, state)
        #
        # # Derive goals; preferred_actions bubble relevant variants to the top
        # try:
        #     stg = self.goal_manager.get_short_term_goal(state, inv)
        #     goals_prompt = self.goal_manager.format_for_prompt(state, inv)
        #     goals_cli = self.goal_manager.format_for_cli(state, inv)
        # except StateFieldError as exc:
        #     logger.error(f"Goal manager failed: {exc}")
        #     logger.error("Fix Lua exporter then resume - emitting random explore")
        #     return self._emit(self._random_explore_action("STATE BROKEN — PAUSE GAME"))
        #
        # logger.debug(goals_cli)
        #
        # # Bubble preferred actions to the top of the concrete list
        # if stg and stg.preferred_actions:
        #     # A preferred prefix matches if the action name matches
        #     def _is_preferred(opt: ActionOption) -> bool:
        #         return any(opt.action == p.split(":")[0] for p in stg.preferred_actions)
        #
        #     preferred = [a for a in concrete_actions if _is_preferred(a)]
        #     rest = [a for a in concrete_actions if not _is_preferred(a)]
        #     action_options_sorted: list[ActionOption] = preferred + rest
        # else:
        #     action_options_sorted: list[ActionOption] = concrete_actions
        #
        # prompt = build_prompt(
        #     state,
        #     self.memory.recent(),
        #     inv,
        #     last_action=self._last_action,
        #     last_action_changed=self._last_action_changed,
        #     world_history=self.world_tracker.summary_lines(state),
        #     valid_actions=action_options_sorted,
        #     goals=goals_prompt,
        # )
        #
        # logger.debug(f" -- LLM Prompt -- \n{60 * '='}\n{prompt}\n{60 * '='}")
        #
        # try:
        #     raw = self.llm_client.generate(prompt)
        #     logger.debug("LLM raw response:\n%s", raw)
        #     action = self.action_parser.parse(raw)
        # except Exception as e:
        #     logger.error(f"LLM call failed: {e}")
        #     logger.warning("Falling back to random explore")
        #     action = self._random_explore_action("LLM unavailable")
        #     raw = None
        #
        # # Validate: check if the LLM's action+target exists in our offered list
        # # Build lookup: action name -> list of ActionOption objects
        # actions_by_name: dict[str, list[ActionOption]] = {}
        # for opt in action_options_sorted:
        #     actions_by_name.setdefault(opt.action, []).append(opt)
        #
        # chosen_action = action["action"]
        # chosen_target = action.get("target")
        #
        # # Check if action name is valid
        # if chosen_action not in actions_by_name:
        #     logger.info(
        #         f"[Agent] INVALID: '{chosen_action}' not in valid_actions — forcing random explore"
        #     )
        #     self.memory.add(
        #         f"Rejected '{chosen_action}' (not in valid actions), forced explore",
        #         "system",
        #     )
        #     action = self._random_explore_action(
        #         f"'{chosen_action}' not a valid action"
        #     )
        # elif chosen_action in actions_by_name:
        #     # Validate target if needed
        #     valid_opts = actions_by_name[chosen_action]
        #     needs_target = any(opt.target is not None for opt in valid_opts)
        #
        #     if needs_target and not chosen_target:
        #         logger.info(
        #             f"[Agent] INVALID: '{chosen_action}' missing required target — forcing random explore"
        #         )
        #         self.memory.add(
        #             f"Rejected '{chosen_action}' (missing target), forced explore",
        #             "system",
        #         )
        #         action = self._random_explore_action(
        #             f"'{chosen_action}' must include a specific target"
        #         )
        #
        # self.conversation_log.record(prompt, raw or "", action)
        #
        # self.memory.add(action["reason"], "llm_reason")

        self.decision_count += 1

        # TODO return self._emit(action)

    def run(self, interval: float = 5.0) -> None:
        """Poll decide() every interval seconds until interrupted."""
        logger.info(
            f"Starting agent - model={self.llm_client.model}, interval={interval}s \nPress Ctrl+C to stop..."
        )

        while True:
            try:
                self.decide()
            except KeyboardInterrupt:
                logger.info(f"Stopped after {self.decision_count} decisions")

            except Exception as exc:
                if self._is_non_retryable_error(exc):
                    logger.critical(
                        f"Fatal non-retryable error in decide().Stopping agent loop. {exc}"
                    )
                    break

                # Keep loop alive on transient failures; LLM failures are already
                # handled in decide(), but this protects the loop from other
                # unexpected retryable exceptions.
                logger.exception(f"Retryable runtime error in decide(): {exc}")
            time.sleep(interval)

    def _select_mid_term_goal(self, state: GameState, inv: dict[str, int]) -> None:
        """Phase 1: Get mid-term goal options, prompt LLM to choose, store selection."""
        logger.info("[Phase 1] Selecting mid-term goal...")

        # Get 2-3 mid-term goal options
        mid_term_goals = self.goal_manager.get_mid_term_goals(state, inv, limit=3)

        if not mid_term_goals:
            logger.warning("No mid-term goals available, skipping goal selection")
            return

        # Format goals for prompt (using GoalManager's formatter)
        goals_prompt = "\n".join(
            f"  {i}. {g.description}" for i, g in enumerate(mid_term_goals, 1)
        )

        # Build goal selection prompt (Phase 1 - no actions needed yet)
        builder = create_default_builder()
        prompt = builder.build(
            state=state,
            valid_actions=[],  # Phase 1: no actions, just goal selection
            goals=goals_prompt,
            memory=self.memory.recent(),
        )

        logger.debug(f"[Goal Selection Prompt]\n{'=' * 60}\n{prompt}\n{'=' * 60}")

        # Call LLM
        raw_response = self.llm_client.generate(prompt)
        if not raw_response:
            raw_response = self._mock_goal_selection_response(mid_term_goals)
            logger.warning(
                f"Ollama unavailable or timed out; using fallback response: '{raw_response}'"
            )
            self.memory.add(
                "Ollama unavailable or timed out; used fallback mid-term goal selection.",
                "mid_term_goal_fallback",
            )

        logger.info(f"LLM raw response: '{raw_response}'")

        # Parse choice and reason
        selected_goal, reason = parse_goal_choice(raw_response, mid_term_goals)

        if selected_goal:
            self._current_mid_term_goal = ActiveGoal(
                goal=selected_goal,
                selected_day=state.day,
                selected_phase=state.phase,
                selection_reason=reason,
            )

            logger.info(
                f"Selected mid-term goal: {selected_goal.description}. -- Reason: {reason}"
            )

            self.memory.add(
                f"Selected mid-term goal: {selected_goal.description} (Reason: {reason})",
                "mid_term_goal",
            )

    def _check_goal_completion(self, state: GameState) -> None:
        """Check if current mid-term goal is completed and clear it if so.

        Called each decision cycle to detect goal completion via predicates.
        Logs completion to memory and clears the goal to trigger reselection.
        """
        if not self._current_mid_term_goal:
            return

        goal_obj = self._current_mid_term_goal.goal
        if goal_obj.goal_check and goal_obj.goal_check(state):
            logger.info(f"Goal completed: {goal_obj.description}")
            self.memory.add(
                f"Completed mid-term goal: {goal_obj.description}",
                "mid_term_goal_completed",
            )
            self._current_mid_term_goal = None  # Clear to trigger reselection

    @staticmethod
    def _is_non_retryable_error(exc: Exception) -> bool:
        """Classify errors that should stop the infinite loop.

        Non-retryable errors are usually deterministic/configuration issues
        that will repeat every tick until fixed (for example unknown season).
        """
        if isinstance(exc, (KeyError, ValueError, NameError)):
            return True
        return False

    @staticmethod
    def _mock_goal_selection_response(mid_term_goals: list[ActiveGoal] | list) -> str:
        """Return a deterministic mocked goal-choice response.

        GoalManager already returns the options in priority order, so choosing the
        first entry preserves current policy without introducing a second planner.
        """
        if not mid_term_goals:
            return "1 - Fallback goal selection unavailable"

        return (
            "1 - Ollama unavailable or timed out, selecting the highest-priority "
            "mid-term goal from the current ordering"
        )

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
        time_of_day = state.time_of_day or 0.0  # None → assume daytime (safe)

        if health < 20:
            logger.warning(f"CRITICAL: Health very low ({health}/150)")
            return {"action": "eat_food", "reason": "Health critically low"}

        if threats:
            t = threats[0]
            tname = (t.name or "unknown").lower()
            tdist = t.distance or "?"
            logger.warning(f"THREAT: {tname} at {tdist}m")
            return {
                "action": "run_from_enemy",
                "reason": f"Hostile {tname} at {tdist}m",
            }

        if time_of_day > 0.75:
            stg = self.goal_manager.get_short_term_goal(state, inv)
            if stg and stg.urgency in (Urgency.CRITICAL, Urgency.URGENT):
                # Pick the first preferred action that's actually craftable
                valid_set = set(self.goal_planner.get_valid_actions(inv))
                for act in stg.preferred_actions:
                    if act in valid_set:
                        logger.warning(f"DUSK/NIGHT: {stg.description[:60]}")
                        return {"action": act, "reason": stg.description}
                # Nothing craftable yet — gather materials
                logger.warning("DUSK/NIGHT: Need fire materials, gathering")
                return {"action": "gather_resource", "reason": stg.description}

        return None

    def _emit(self, action: dict) -> dict:
        self._last_action = action["action"]
        self.action_writer.write(action)
        return action
