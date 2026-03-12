"""E2E tests for strategic LLM goal selection and GOAP execution."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that returns predefined goal choices."""
    mock = Mock()
    
    def set_response(goal: str, reason: str = "Test reason"):
        """Configure mock to return specific goal."""
        mock.call.return_value = f'{{"goal": "{goal}", "reason": "{reason}"}}'
    
    mock.set_response = set_response
    return mock


@pytest.mark.skip(reason="Requires strategic_goals.py and goap_executor.py implementation")
def test_day1_picks_gather_basic_resources(agent, day1_fresh, mock_llm_client):
    """Day 1 empty inventory → LLM should pick gather_basic_resources goal."""
    mock_llm_client.set_response("gather_basic_resources", "Need tools for survival")
    
    with patch.object(agent, 'llm_client', mock_llm_client):
        inv = agent.inventory_tracker.update(day1_fresh)
        action = agent.decide(day1_fresh, inv)
    
    # Should pick up flint (first step toward making axe)
    assert action is not None
    assert action["action"] == "pick_up_item"
    assert "flint" in action["target"]


@pytest.mark.skip(reason="Requires strategic_goals.py and goap_executor.py implementation")
def test_dusk_picks_prepare_for_night(agent, day2_spring_inventory, mock_llm_client):
    """Dusk approaching → LLM should prioritize prepare_for_night."""
    state = day2_spring_inventory.model_copy(update={
        "phase": "dusk",
        "equipped": None,
        "inventory": ["twigs x5", "cutgrass x3"]
    })
    
    mock_llm_client.set_response("prepare_for_night", "Dark soon, need light")
    
    with patch.object(agent, 'llm_client', mock_llm_client):
        inv = agent.inventory_tracker.update(state)
        action = agent.decide(state, inv)
    
    # Should craft torch (has materials)
    assert action is not None
    assert action["action"] == "craft_item"
    assert action["target"] == "torch"


@pytest.mark.skip(reason="Requires strategic_goals.py and goap_executor.py implementation")
def test_late_autumn_picks_prepare_for_winter(agent, winter_stocked, mock_llm_client):
    """Late autumn → should pick prepare_for_winter goal."""
    state = winter_stocked.model_copy(update={
        "season": "autumn",
        "day": 14,  # Near end of autumn (assume 16 days)
        "inventory": ["log x10", "twigs x8", "rope x2"]
    })
    
    mock_llm_client.set_response("prepare_for_winter", "Winter approaching, need warm gear")
    
    with patch.object(agent, 'llm_client', mock_llm_client):
        inv = agent.inventory_tracker.update(state)
        action = agent.decide(state, inv)
    
    # Should work toward thermal stone or warm clothing
    assert action is not None
    # Exact action depends on GOAP prereq resolution


@pytest.mark.skip(reason="Requires GOAP completion detection")
def test_goal_completion_triggers_reevaluation(agent, day1_fresh, mock_llm_client):
    """When goal completes, agent should re-evaluate and pick new goal."""
    # Simulate: agent has axe → gather_basic_resources complete
    state = day1_fresh.model_copy(update={
        "inventory": ["axe", "pickaxe", "torch", "berries x10"]
    })
    
    mock_llm_client.set_response("establish_base", "Got tools, time to build")
    
    with patch.object(agent, 'llm_client', mock_llm_client):
        inv = agent.inventory_tracker.update(state)
        action = agent.decide(state, inv)
    
    # Should move to next strategic phase
    assert action is not None
    # Should craft science machine or firepit components


@pytest.mark.skip(reason="Requires stuck detection logic")
def test_blocked_goal_falls_back_to_explore(agent, day2_spring_inventory, mock_llm_client):
    """If goal blocked (missing resources), fallback to explore."""
    # Simulate: picked "establish_base" but no logs nearby
    state = day2_spring_inventory.model_copy(update={
        "inventory": ["twigs x20", "flint x5"],  # No logs
        "nearby_entities": []  # Nothing harvestable
    })
    
    mock_llm_client.set_response("establish_base", "Build firepit")
    
    with patch.object(agent, 'llm_client', mock_llm_client):
        inv = agent.inventory_tracker.update(state)
        action = agent.decide(state, inv)
    
    # Can't build firepit (need logs), should explore
    assert action is not None
    assert action["action"] == "explore"
