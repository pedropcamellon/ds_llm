#!/usr/bin/env python3
"""
llm_agent.py — Orchestrator. Coordinates collaborators to produce one action per tick.

All I/O, HTTP, parsing, and memory concerns are delegated to injected collaborators
(see main.py for wiring). This class only contains the decision loop.
"""

import time

from action_parser import ActionParser
from action_writer import ActionWriter
from memory import AgentMemory
from ollama_client import OllamaClient
from prompt import build_prompt
from state_reader import StateReader


class DSAIAgent:
    def __init__(
        self,
        state_reader: StateReader,
        memory: AgentMemory,
        llm_client: OllamaClient,
        action_parser: ActionParser,
        action_writer: ActionWriter,
    ):
        self.state_reader = state_reader
        self.memory = memory
        self.llm_client = llm_client
        self.action_parser = action_parser
        self.action_writer = action_writer
        self.decision_count = 0

    # ------------------------------------------------------------------
    # Decision logic
    # ------------------------------------------------------------------

    def decide(self) -> dict | None:
        """Read game state, apply emergency overrides, call LLM, write action."""
        state = self.state_reader.read()
        if not state:
            print("[Agent] Cannot read game state, idling...")
            return self._emit({"action": "idle", "reason": "No game state available"})

        if not self.state_reader.has_changed(state):
            print("[Agent] State unchanged, skipping decision")
            return None

        if self.state_reader.is_world_reset(state):
            self.memory.clear()
            self.memory.add("World reset! Starting fresh.", "system")

        # Emergency fast-path overrides (no LLM call needed)
        override = self._emergency_override(state)
        if override:
            return self._emit(override)

        # Normal path: ask the LLM
        prompt = build_prompt(state, self.memory.recent())
        raw = self.llm_client.generate(prompt)
        action = self.action_parser.parse(raw)

        if action["action"] != "idle":
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

    def _emergency_override(self, state: dict) -> dict | None:
        """Return a hardcoded action for critical situations, or None."""
        health = state.get("health", 100)
        threats = state.get("threats", [])
        time_of_day = state.get("time_of_day", 0.0)
        equipped = state.get("equipped", "")

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

        if time_of_day > 0.75 and equipped != "torch":
            print("[Agent] DUSK/NIGHT: Need light!")
            return {"action": "explore", "reason": "Dusk approaching, no light source"}

        return None

    def _emit(self, action: dict) -> dict:
        self.action_writer.write(action)
        return action
