"""
pipeline.py — Orchestrates the agent decision pipeline.

Loads state, runs modules (inventory, goals, actions, prompt), and returns
results. Single Responsibility: pipeline execution only.
"""

from pathlib import Path

from action_planner import ActionPlanner
from goal_manager import GoalManager
from inventory_tracker import InventoryTracker
from memory import AgentMemory
from models import GameState
from prompt import build_prompt
from world_tracker import WorldTracker


class PipelineResult:
    """Container for pipeline execution results."""

    def __init__(
        self,
        state: GameState,
        inv,
        goals_text: str,
        short_term_goal,
        concrete_actions: list,
        prompt_text: str,
        world_history: list[str],
    ):
        self.state = state
        self.inv = inv
        self.goals_text = goals_text
        self.short_term_goal = short_term_goal
        self.concrete_actions = concrete_actions
        self.prompt_text = prompt_text
        self.world_history = world_history


class DebugPipeline:
    """Executes the full agent pipeline for a given game state."""

    def __init__(self, memory_path: Path | None = None):
        """Initialize pipeline with optional memory path."""
        if memory_path is None:
            memory_path = Path("_debug_memory.jsonl")

        self.inv_tracker = InventoryTracker(AgentMemory(memory_path))
        self.world_tracker = WorldTracker(ttl_seconds=120.0)
        self.goal_manager = GoalManager()
        self.action_planner = ActionPlanner()

    def run(self, state: GameState) -> PipelineResult:
        """
        Run the full pipeline: inventory → goals → actions → prompt.

        Returns PipelineResult with all computed values.
        """
        # Update trackers
        inv = self.inv_tracker.update(state)
        self.world_tracker.update(state)

        # Compute goals
        goals_text = self.goal_manager.format_for_prompt(state, inv)
        short_term_goal = self.goal_manager.get_short_term_goal(state, inv)

        # Build action list
        concrete_actions = self.action_planner.get_concrete_actions(inv, state)

        # Generate prompt
        world_history = self.world_tracker.summary_lines(state)
        prompt_text = build_prompt(
            state,
            memory=[],  # no memory for single-shot debug
            inv=inv,
            valid_actions=concrete_actions,
            goals=goals_text,
            world_history=world_history,
        )

        return PipelineResult(
            state=state,
            inv=inv,
            goals_text=goals_text,
            short_term_goal=short_term_goal,
            concrete_actions=concrete_actions,
            prompt_text=prompt_text,
            world_history=world_history,
        )
