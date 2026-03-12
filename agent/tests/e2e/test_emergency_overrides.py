"""E2E tests for emergency override behavior — bypasses LLM for critical situations."""

import pytest
from pathlib import Path
from llm_agent import DSAIAgent
from state_reader import StateReader
from memory import AgentMemory
from ollama_client import OllamaClient
from action_parser import ActionParser
from action_writer import ActionWriter
from inventory_tracker import InventoryTracker
from conversation_log import ConversationLog
from world_tracker import WorldTracker
from action_planner import ActionPlanner
from goal_manager import GoalManager


@pytest.fixture
def agent(tmp_path):
    """Create agent instance for testing (real modules, no mocks)."""
    state_file = tmp_path / "game_state.json"
    memory_file = tmp_path / "memory.jsonl"
    action_file = tmp_path / "action.json"
    convo_file = tmp_path / "conversation.jsonl"

    return DSAIAgent(
        state_reader=StateReader(state_file),
        memory=AgentMemory(memory_file),
        llm_client=OllamaClient(model="gemma3:1b"),  # Won't be called for emergencies
        action_parser=ActionParser(),
        action_writer=ActionWriter(action_file),
        inventory_tracker=InventoryTracker(AgentMemory(memory_file)),
        conversation_log=ConversationLog(convo_file),
        world_tracker=WorldTracker(),
        goal_planner=ActionPlanner(),
        goal_manager=GoalManager(),
    )


def test_low_health_forces_eat_food(agent, low_health_hostile):
    """Health < 20 → must eat food, even with hostile nearby."""
    # Ensure state has edible food in inventory
    state = low_health_hostile.model_copy(
        update={"health": 15.0, "inventory": ["berries x3", "twigs x5"]}
    )

    inv = agent.inventory_tracker.update(state)
    action = agent.decide(state, inv)

    # Should prioritize eating over running (health is CRITICAL)
    assert action is not None
    assert action["action"] == "eat_food"
    assert "berries" in action["target"]


def test_threats_force_flee(agent, low_health_hostile):
    """Hostile nearby → run_from_enemy (unless health critical)."""
    state = low_health_hostile.model_copy(
        update={
            "health": 50.0,  # Not critical
            "threats": [{"name": "spider", "distance": 8.0}],
        }
    )

    inv = agent.inventory_tracker.update(state)
    action = agent.decide(state, inv)

    assert action is not None
    assert action["action"] == "run_from_enemy"


def test_night_no_light_force_torch(agent, night_no_fire):
    """Night phase without equipped light → craft torch or find campfire."""
    state = night_no_fire.model_copy(
        update={
            "phase": "night",
            "equipped": None,
            "inventory": ["twigs x2", "cutgrass x2"],
        }
    )

    inv = agent.inventory_tracker.update(state)
    action = agent.decide(state, inv)

    assert action is not None
    # Should craft torch (has ingredients) or explore to campfire
    assert action["action"] in ["craft_item", "explore"]
    if action["action"] == "craft_item":
        assert action["target"] == "torch"


def test_emergency_bypasses_llm(agent, low_health_hostile):
    """Emergency situations should NOT call LLM (too slow)."""
    state = low_health_hostile.model_copy(update={"health": 10.0})

    llm_calls_before = agent.llm_call_count
    inv = agent.inventory_tracker.update(state)
    action = agent.decide(state, inv)

    # LLM should not be invoked for emergency
    assert agent.llm_call_count == llm_calls_before
    assert action is not None  # Should still return an action


@pytest.mark.parametrize(
    "health,hunger,expected_action",
    [
        (15, 100, "eat_food"),  # Critical health
        (50, 5, "eat_food"),  # Critical hunger
        (10, 10, "eat_food"),  # Both critical → health wins
    ],
)
def test_health_vs_hunger_priority(
    agent, day2_spring_inventory, health, hunger, expected_action
):
    """Test priority order: critical health > critical hunger > threats > night."""
    state = day2_spring_inventory.model_copy(
        update={"health": health, "hunger": hunger, "inventory": ["berries x5"]}
    )

    inv = agent.inventory_tracker.update(state)
    action = agent.decide(state, inv)

    assert action is not None
    assert action["action"] == expected_action
