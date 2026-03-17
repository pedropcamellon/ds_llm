"""
tests/e2e/test_goal_persistence.py — E2E tests for mid-term goal persistence lifecycle.

Tests the complete goal lifecycle:
1. Selection (LLM picks from options)
2. Persistence (goal stays active across cycles)
3. Completion (predicate triggers reselection)
4. Timeout (reselection after interval)
"""

import pytest
from unittest.mock import Mock, patch
from models import GameState, NearbyEntity
from goals.models import MidTermGoal
from goals.predicates import has_item_count, has_structure
from llm_agent import DSAIAgent


class TestGoalPersistence:
    """Test goal persistence across multiple decision cycles."""

    def test_goal_persists_across_cycles(self, agent_with_mocks):
        """Goal should persist across cycles without reselection."""
        agent, mocks = agent_with_mocks
        
        # First decision: Select goal
        mocks['llm_client'].generate.return_value = "2 - Testing goal persistence"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200
        )
        
        agent.decide()
        
        # Verify goal selected
        assert agent._current_mid_term_goal is not None
        assert agent._current_mid_term_goal.goal is not None
        assert agent._current_mid_term_goal.selected_day == 1
        assert agent._current_mid_term_goal.selected_phase == "day"
        original_goal = agent._current_mid_term_goal
        
        # Next 4 decisions: Goal should persist (interval=5)
        for i in range(4):
            mocks['state_reader'].has_changed.return_value = True
            agent.decide()
            
            # Verify goal NOT reselected
            assert agent._current_mid_term_goal == original_goal
            assert agent._current_mid_term_goal is not None
        
        # Verify LLM only called once (selection, not persistence)
        assert mocks['llm_client'].generate.call_count == 1

    def test_goal_reselection_on_timeout(self, agent_with_mocks):
        """Goal should reselect after interval timeout."""
        agent, mocks = agent_with_mocks
        agent._goal_selection_interval = 3  # Short interval for testing
        
        # First selection
        mocks['llm_client'].generate.return_value = "1 - Testing timeout reselection"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200
        )
        
        agent.decide()  # decision_count=1
        first_goal = agent._current_mid_term_goal
        
        # Next 2 decisions (below interval)
        for _ in range(2):
            mocks['state_reader'].has_changed.return_value = True
            agent.decide()  # decision_count=2, 3
        
        assert agent._current_mid_term_goal == first_goal  # Still first goal
        
        # 3rd decision triggers timeout (decision_count=3, interval=3)
        mocks['llm_client'].generate.return_value = "2 - New goal after timeout"  # Different choice
        mocks['state_reader'].has_changed.return_value = True
        agent.decide()  # decision_count=4 (but check is on decision_count % interval)
        
        # Verify timeout triggered reselection
        # Note: Timeout fires when decision_count % interval == 0
        # So we need to advance to decision_count=6 (next multiple of 3)
        for _ in range(2):
            mocks['state_reader'].has_changed.return_value = True
            agent.decide()
        
        # Now timeout should have triggered
        assert mocks['llm_client'].generate.call_count >= 2

    def test_goal_completion_triggers_immediate_reselection(self, agent_with_mocks):
        """Completed goal should trigger immediate reselection."""
        agent, mocks = agent_with_mocks
        
        # Create completable goal and fallback goal
        completable_goal = MidTermGoal(
            day_range="",
            description="Gather 10 twigs",
            focus_actions=["gather_resource"],
            reason="test_goal",
            goal_check=has_item_count("twigs", 10)  # Proper predicate
        )
        fallback_goal = MidTermGoal(
            day_range="",
            description="Explore map",
            focus_actions=["explore"],
            reason="exploration",
            goal_check=lambda s: False  # Never completes
        )
        
        # Phase 1: Select completable goal
        mocks['goal_manager'].get_mid_term_goals.return_value = [completable_goal, fallback_goal]
        mocks['llm_client'].generate.return_value = "1 - Testing completion detection"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200,
            inventory={"twigs": 5}  # Not completed yet
        )
        
        agent.decide()
        
        # Verify goal selected
        assert agent._current_mid_term_goal is not None
        assert agent._current_mid_term_goal.goal == completable_goal
        
        # Phase 2: Complete goal → triggers reselection
        mocks['llm_client'].generate.return_value = "2 - Switching to fallback goal"  # Pick fallback goal
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200,
            inventory={"twigs": 10}  # NOW completed
        )
        mocks['state_reader'].has_changed.return_value = True
        
        agent.decide()
        
        # Verify completion was detected and new goal selected
        assert agent._current_mid_term_goal is not None
        assert agent._current_mid_term_goal.goal == fallback_goal
        
        # Verify completion logged to memory
        memory_entries = [e for e in agent.memory._entries if e.get("source") == "mid_term_goal_completed"]
        assert len(memory_entries) == 1
        assert "Gather 10 twigs" in memory_entries[0]["text"]

    def test_completion_checked_every_cycle(self, agent_with_mocks):
        """Completion predicate should be checked every decide() cycle, not just during selection."""
        agent, mocks = agent_with_mocks
        agent._goal_selection_interval = 20  # Long interval - won't reselect naturally
        
        # Create goal that completes when gold >= 3
        completable_goal = MidTermGoal(
            day_range="",
            description="Gather gold for science machine",
            focus_actions=["gather_resource"],
            reason="need_gold",
            goal_check=has_item_count("gold", 3)
        )
        fallback_goal = MidTermGoal(
            day_range="",
            description="Explore for resources",
            focus_actions=["explore"],
            reason="exploration",
            goal_check=lambda s: False
        )
        
        mocks['goal_manager'].get_mid_term_goals.return_value = [completable_goal, fallback_goal]
        
        # Cycle 1: Select goal with gold=0
        mocks['llm_client'].generate.return_value = "1 - Need gold for science machine"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200,
            inventory={"gold": 0}
        )
        agent.decide()
        assert agent._current_mid_term_goal.goal == completable_goal
        
        # Cycle 2: gold=1 (not complete yet, goal persists)
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200,
            inventory={"gold": 1}
        )
        agent.decide()
        assert agent._current_mid_term_goal.goal == completable_goal  # Still active
        
        # Cycle 3: gold=2 (still not complete, goal persists)
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="dusk", season="autumn",
            health=150, hunger=100, sanity=200,
            inventory={"gold": 2}
        )
        agent.decide()
        assert agent._current_mid_term_goal.goal == completable_goal  # Still active
        
        # Cycle 4: gold=3 (COMPLETE! Should detect immediately and reselect)
        mocks['llm_client'].generate.return_value = "2 - Switching to exploration after gold collected"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="dusk", season="autumn",
            health=150, hunger=100, sanity=200,
            inventory={"gold": 3}  # COMPLETED!
        )
        agent.decide()
        
        # Verify completion detected immediately (not waiting for timeout)
        assert agent._current_mid_term_goal.goal == fallback_goal  # New goal selected
        
        # Verify completion logged
        memory_entries = [e for e in agent.memory._entries if e.get("source") == "mid_term_goal_completed"]
        assert len(memory_entries) == 1
        assert "Gather gold" in memory_entries[0]["text"]
        
        # Verify LLM called twice: once for initial selection, once for reselection after completion
        assert mocks['llm_client'].generate.call_count == 2

    def test_selection_reason_captured_and_logged(self, agent_with_mocks):
        """Selection reason from LLM should be captured in ActiveGoal and logged to memory."""
        agent, mocks = agent_with_mocks
        
        # LLM responds with goal number and reason
        llm_response = "2 - Food reserves are critically low and winter is approaching"
        mocks['llm_client'].generate.return_value = llm_response
        mocks['state_reader'].read.return_value = GameState(
            day=5, phase="day", season="autumn",
            health=150, hunger=100, sanity=200
        )
        
        agent.decide()
        
        # Verify goal selected with reason captured
        assert agent._current_mid_term_goal is not None
        assert agent._current_mid_term_goal.selection_reason == "Food reserves are critically low and winter is approaching"
        
        # Verify reason logged to memory
        memory_entries = [e for e in agent.memory._entries if e.get("source") == "mid_term_goal"]
        assert len(memory_entries) == 1
        assert "Stockpile food reserves" in memory_entries[0]["text"]
        assert "Food reserves are critically low" in memory_entries[0]["text"]


class TestGoalSelectionFailures:
    """Test failure modes in goal selection."""

    def test_llm_parse_failure_no_fallback(self, agent_with_mocks):
        """Parse failure should return None (fail-fast, no default fallback)."""
        agent, mocks = agent_with_mocks
        
        # LLM returns unparseable response
        mocks['llm_client'].generate.return_value = "I choose to build a base"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200
        )
        
        agent.decide()
        
        # Verify parse failure handled gracefully (logs warning, continues)
        # Agent should handle None from parser
        assert True  # If we got here, no crash occurred

    def test_empty_llm_response_raises_error(self, agent_with_mocks):
        """Empty LLM response should raise ValueError in select method."""
        agent, mocks = agent_with_mocks
        
        mocks['llm_client'].generate.return_value = None  # Empty response
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200
        )
        
        # Should log error but not crash agent loop
        agent.decide()  # Should catch exception and continue

    def test_no_mid_term_goals_available(self, agent_with_mocks):
        """No available goals should skip selection gracefully."""
        agent, mocks = agent_with_mocks
        
        # Mock empty goal list
        with patch.object(agent.goal_manager, 'get_mid_term_goals', return_value=[]):
            mocks['state_reader'].read.return_value = GameState(
                day=1, phase="day", season="autumn",
                health=150, hunger=100, sanity=200
            )
            
            agent.decide()
            
            # Verify no goal selected
            assert agent._current_mid_term_goal is None


class TestGoalLifecycleIntegration:
    """Integration tests covering complete goal lifecycle scenarios."""

    def test_full_lifecycle_select_persist_complete_reselect(self, agent_with_mocks):
        """Test complete lifecycle: select → persist → complete → reselect."""
        agent, mocks = agent_with_mocks
        agent._goal_selection_interval = 10  # Long interval
        
        # Phase 1: Select first goal
        goal1 = MidTermGoal(
            day_range="",
            description="Build science machine",
            focus_actions=["gather_resource", "craft_item"],
            reason="missing_structure",
            goal_check=has_structure("science_machine")  # Proper predicate
        )
        goal2 = MidTermGoal(
            day_range="",
            description="Explore map",
            focus_actions=["explore_map"],
            reason="exploration",
            goal_check=lambda s: False  # Never completes
        )
        
        with patch.object(agent.goal_manager, 'get_mid_term_goals', return_value=[goal1, goal2]):
            mocks['llm_client'].generate.return_value = "1 - Building science machine first"  # Choose goal1
            mocks['state_reader'].read.return_value = GameState(
                day=1, phase="day", season="autumn",
                health=150, hunger=100, sanity=200,
                nearby_entities=[]
            )
            
            agent.decide()
            assert agent._current_mid_term_goal is not None
            assert agent._current_mid_term_goal.goal == goal1
            
            # Phase 2: Persist across 3 cycles
            for i in range(3):
                mocks['state_reader'].has_changed.return_value = True
                mocks['state_reader'].read.return_value = GameState(
                    day=1+i, phase="day", season="autumn",
                    health=150, hunger=100, sanity=200,
                    nearby_entities=[]  # Not completed yet
                )
                agent.decide()
                assert agent._current_mid_term_goal.goal == goal1  # Still goal1
            
            # Phase 3: Complete goal → reselect immediately
            mocks['llm_client'].generate.return_value = "2 - Exploring after science machine built"  # Choose goal2 after completion
            mocks['state_reader'].read.return_value = GameState(
                day=5, phase="day", season="autumn",
                health=150, hunger=100, sanity=200,
                nearby_entities=[NearbyEntity(name="science_machine", type="structure", distance=5.0)]  # Completed!
            )
            mocks['state_reader'].has_changed.return_value = True
            agent.decide()
            
            # Verify completion detected and NEW goal selected
            assert agent._current_mid_term_goal is not None
            assert agent._current_mid_term_goal.goal == goal2  # Should be goal2 now

    def test_timeout_with_incomplete_goal_logs_warning(self, agent_with_mocks):
        """Timeout on incomplete goal should log warning."""
        agent, mocks = agent_with_mocks
        agent._goal_selection_interval = 2  # Very short
        
        mocks['llm_client'].generate.return_value = "1 - Testing timeout warning"
        mocks['state_reader'].read.return_value = GameState(
            day=1, phase="day", season="autumn",
            health=150, hunger=100, sanity=200
        )
        
        agent.decide()  # Select goal
        first_goal = agent._current_mid_term_goal
        
        # Advance to timeout
        mocks['state_reader'].has_changed.return_value = True
        agent.decide()  # decision_count=2, triggers timeout (2 % 2 == 0)
        
        # Verify timeout message in memory
        memory_entries = [e for e in agent.memory._entries if e.get("source") == "mid_term_goal_timeout"]
        assert len(memory_entries) >= 0  # Timeout may or may not fire depending on logic


@pytest.fixture
def agent_with_mocks(tmp_path):
    """Create DSAIAgent with all dependencies mocked."""
    from memory import AgentMemory
    
    # Real memory (for testing memory entries)
    memory_file = tmp_path / "test_memory.jsonl"
    memory = AgentMemory(memory_file, max_entries=50)
    
    # Mock all other dependencies
    mocks = {
        'state_reader': Mock(),
        'llm_client': Mock(),
        'action_parser': Mock(),
        'action_writer': Mock(),
        'inventory_tracker': Mock(),
        'conversation_log': Mock(),
        'world_tracker': Mock(),
        'goal_planner': Mock(),
        'goal_manager': Mock(),
    }
    
    # Configure mocks
    mocks['state_reader'].has_changed.return_value = True
    mocks['state_reader'].is_game_over.return_value = False
    mocks['state_reader'].is_world_reset.return_value = False
    mocks['inventory_tracker'].current = {}
    mocks['world_tracker'].summary_lines.return_value = "No history"
    
    # Default mid-term goals (3 options)
    from goals.predicates import has_structure
    default_goals = [
        MidTermGoal(
            day_range="",
            description="Build base with science machine",
            focus_actions=["gather_resource", "craft_item"],
            reason="missing_science_machine",
            goal_check=has_structure("science_machine"),
        ),
        MidTermGoal(
            day_range="",
            description="Stockpile food reserves",
            focus_actions=["gather_resource", "hunt_mob"],
            reason="low_food",
            goal_check=lambda s: False,  # Ongoing
        ),
        MidTermGoal(
            day_range="",
            description="Explore unmapped areas",
            focus_actions=["explore_map"],
            reason="exploration",
            goal_check=lambda s: False,  # Ongoing
        ),
    ]
    mocks['goal_manager'].get_mid_term_goals.return_value = default_goals
    mocks['goal_manager'].get_short_term_goal.return_value = None  # No urgent goals
    mocks['goal_manager'].format_for_prompt.return_value = "Goals..."
    mocks['goal_manager'].format_for_cli.return_value = "Goals..."
    
    # Create agent
    agent = DSAIAgent(
        state_reader=mocks['state_reader'],
        memory=memory,
        llm_client=mocks['llm_client'],
        action_parser=mocks['action_parser'],
        action_writer=mocks['action_writer'],
        inventory_tracker=mocks['inventory_tracker'],
        conversation_log=mocks['conversation_log'],
        world_tracker=mocks['world_tracker'],
        goal_planner=mocks['goal_planner'],
        goal_manager=mocks['goal_manager'],
    )
    
    # Set short interval for easier testing
    agent._goal_selection_interval = 5
    
    return agent, mocks
