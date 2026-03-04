"""
prereq_filter.py — PrereqFilter: inventory-based action gating.

Single responsibility: given an inventory, decide which base actions are
valid (prereqs met) and which are blocked (prereqs missing), and format
both for insertion into the LLM prompt.

Does NOT know anything about nearby entities, food choices, or enemies.
That belongs in ConcreteActionBuilder.
"""

from action_specs import (
    ACTION_SPECS,
    PREFAB_ALIASES,
    ActionSpec,
    has_prereqs,
    missing_items,
    normalize_inv,
)


class PrereqFilter:
    """Filters the base ACTION_SPECS catalogue by current inventory."""

    def __init__(self, specs: dict[str, ActionSpec] | None = None) -> None:
        self.specs: dict[str, ActionSpec] = specs or ACTION_SPECS

    # ------------------------------------------------------------------
    # Core filtering
    # ------------------------------------------------------------------

    def get_valid_actions(self, inv: dict[str, int]) -> list[str]:
        """Actions whose prerequisites are satisfied by *inv* and that aren't redundant.

        Redundant = craft action with redundant_if_held=True whose output is
        already present in inventory (e.g. don't offer craft_item:axe when axe
        is already held).
        """
        inv_norm = normalize_inv(inv)
        result = []
        for action, spec in self.specs.items():
            if not has_prereqs(inv_norm, spec.requires):
                continue
            if spec.redundant_if_held and all(
                inv_norm.get(item, 0) >= 1 for item in spec.provides
            ):
                continue  # already own the output — no point crafting
            result.append(action)
        return result

    # ------------------------------------------------------------------
    # Prompt formatting
    # ------------------------------------------------------------------

    def format_valid_actions(self, inv: dict[str, int]) -> str:
        """Sorted comma-separated list; craft_item entries include ingredient costs."""
        parts: list[str] = []
        for action in sorted(self.get_valid_actions(inv)):
            spec = self.specs[action]
            if action.startswith("craft_item:") and spec.requires:
                cost = "+".join(f"{k}×{v}" for k, v in spec.requires.items())
                parts.append(f"{action} ({cost})")
            else:
                parts.append(action)
        return ", ".join(parts)
