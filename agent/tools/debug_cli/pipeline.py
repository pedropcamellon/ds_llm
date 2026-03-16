"""
pipeline.py — Black-box agent runner for debug CLI.

Treats agent as opaque: feed it state, get back action decision.
No direct access to internal trackers/managers.
"""

from pathlib import Path

from llm_agent import DSAIAgent
from action_parser import ActionParser
from action_writer import ActionWriter
from conversation_log import ConversationLog
from action_planner import ActionPlanner
from goal_manager import GoalManager
from inventory_tracker import InventoryTracker
from memory import AgentMemory
from models import GameState
from ollama_client import OllamaClient
from state_reader import StateReader
from world_tracker import WorldTracker
from strategic_goals import get_suggested_goals
from goap_executor import get_next_action_for_goal


class DebugResult:
    """Container for agent decision result."""

    def __init__(
        self,
        state: GameState,
        action: dict | None,
        mode: str,
        current_goal: str | None = None,
        llm_called: bool = False,
        prompt_text: str | None = None,
        suggested_goals: list[str] | None = None,
        llm_reason: str | None = None,
        goap_chain: list[str] | None = None,
    ):
        self.state = state
        self.action = action
        self.mode = mode
        self.current_goal = current_goal
        self.llm_called = llm_called
        self.prompt_text = prompt_text
        self.suggested_goals = suggested_goals  # Goals offered to LLM
        self.llm_reason = llm_reason  # Why LLM chose this goal
        self.goap_chain = goap_chain  # Steps GOAP planned


class DebugPipeline:
    """Black-box agent executor for testing."""

    def __init__(self, state_path: Path, memory_path: Path | None = None, model: str = "gemma3:1b"):
        """Initialize agent with debug mode."""
        if memory_path is None:
            memory_path = Path("_debug_memory.jsonl")

        self.agent = DSAIAgent(
            state_reader=StateReader(state_path),
            memory=AgentMemory(memory_path),
            llm_client=OllamaClient(model=model, url="http://localhost:11434"),
            action_parser=ActionParser(),
            action_writer=ActionWriter(state_path.parent / "_debug_action.json"),
            inventory_tracker=InventoryTracker(AgentMemory(memory_path)),
            conversation_log=ConversationLog(state_path.parent / "_debug_conversation.jsonl"),
            world_tracker=WorldTracker(ttl_seconds=120.0),
            goal_planner=ActionPlanner(),
            goal_manager=GoalManager(),
        )

    def run(self, state: GameState, mode: str = "full", force_goal: str | None = None) -> DebugResult:
        """
        Run agent decision as black box.

        Args:
            state: Game state to process
            mode: "full" (normal decide), "llm" (force strategic), "goap" (force GOAP)
            force_goal: Optional goal to set for GOAP mode

        Returns:
            DebugResult with action and metadata
        """
        # Write state to file so agent can read it
        import json
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else vars(state)
        with open(self.agent.state_reader.state_file, 'w') as f:
            json.dump(state_dict, f, indent=2, default=str)

        # Capture state before decide()
        llm_count_before = self.agent.llm_call_count

        # Track suggested goals and GOAP chain for visibility
        suggested_goals = None
        llm_reason = None
        goap_chain = None

        inv = self.agent.inventory_tracker.update(state)
        
        # Extract nearby items for GOAP
        nearby_items = [e.get("name", "") for e in state.nearby_entities if e.get("name")]

        if mode == "llm":
            # Get suggested goals BEFORE calling LLM (for display)
            threats_nearby = bool(state.threats)
            suggested = get_suggested_goals(
                phase=state.phase,
                health=state.health,
                hunger=state.hunger,
                inv=inv,
                threats_nearby=threats_nearby,
            )
            suggested_goals = [g.name for g in suggested]

            # Force strategic LLM call
            self.agent._current_goal = None  # Trigger LLM
            action = self.agent._strategic_decide(state, inv, phase_changed=True)

            # Extract LLM reason from conversation log
            if self.agent.conversation_log.log_file.exists():
                try:
                    with open(self.agent.conversation_log.log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            last_entry = json.loads(lines[-1])
                            response = last_entry.get("response", "")
                            # Extract reason from JSON response
                            import re
                            match = re.search(r'"reason"\s*:\s*"([^"]+)"', response)
                            if match:
                                llm_reason = match.group(1)
                except:
                    pass

            # Now run GOAP to get execution chain
            if self.agent._current_goal:
                goap_plan = get_next_action_for_goal(
                    self.agent._current_goal, state, inv, nearby_items
                )
                if goap_plan.steps:
                    goap_chain = goap_plan.steps

        elif mode == "goap":
            # Force GOAP with optional goal
            if force_goal:
                self.agent._current_goal = force_goal
            elif not self.agent._current_goal:
                # Default to gather_basics if no goal set
                self.agent._current_goal = "gather_basics"
            action = self.agent._goap_decide(state, inv)

            # Capture GOAP chain for display
            if self.agent._current_goal:
                goap_plan = get_next_action_for_goal(
                    self.agent._current_goal, state, inv, nearby_items
                )
                if goap_plan.steps:
                    goap_chain = goap_plan.steps
        else:
            # Normal decide() but disable LLM throttling
            # Set a goal so it doesn't try to call LLM
            if not self.agent._current_goal:
                self.agent._current_goal = "gather_basics"
            action = self.agent.decide()

        llm_called = self.agent.llm_call_count > llm_count_before

        # Get last prompt from conversation log if LLM was called
        prompt_text = None
        if llm_called and self.agent.conversation_log.log_file.exists():
            try:
                with open(self.agent.conversation_log.log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        prompt_text = last_entry.get("prompt")
            except:
                pass

        return DebugResult(
            state=state,
            action=action,
            mode=mode,
            current_goal=self.agent._current_goal,
            llm_called=llm_called,
            prompt_text=prompt_text,
            suggested_goals=suggested_goals,
            llm_reason=llm_reason,
            goap_chain=goap_chain,
        )

