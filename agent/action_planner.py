"""
action_planner.py — ActionPlanner: the public façade for the planner subsystem.

Composes PrereqFilter (what is possible?) with ConcreteActionBuilder
(what exactly should the LLM see?) behind a single stable interface.

Callers import only this module — they never depend on the internals.
"""

from action_specs import ACTION_SPECS, ActionSpec
from models import ActionOption, GameState
from concrete_action_builder import ConcreteActionBuilder
from prereq_filter import PrereqFilter


class ActionPlanner:
    """Public façade: prerequisite filtering + concrete action generation.

    Args:
        specs:  Optional override for the base ACTION_SPECS catalogue.
                Pass a custom dict to extend or replace actions in tests.
    """

    def __init__(self, specs: dict[str, ActionSpec] | None = None) -> None:
        effective = specs or ACTION_SPECS
        self._prereq = PrereqFilter(effective)
        self._builder = ConcreteActionBuilder(self._prereq)

        # Expose specs for callers that inspect individual entries
        # (e.g. llm_agent reading craft costs for prompt annotation)
        self.specs: dict[str, ActionSpec] = effective

    # ------------------------------------------------------------------
    # Delegated PrereqFilter API
    # ------------------------------------------------------------------

    def get_valid_actions(self, inv: dict[str, int]) -> list[str]:
        """Base actions whose prerequisites are met by *inv*."""
        return self._prereq.get_valid_actions(inv)

    def format_valid_actions(self, inv: dict[str, int]) -> str:
        return self._prereq.format_valid_actions(inv)

    # ------------------------------------------------------------------
    # Delegated ConcreteActionBuilder API
    # ------------------------------------------------------------------

    def get_concrete_actions(
        self, inv: dict[str, int], state: GameState
    ) -> list[ActionOption]:
        """Specific, labelled actions derived from inventory + live game state."""
        return self._builder.build(inv, state)
