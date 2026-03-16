"""
actions.py — Valid actions section.
"""

import re
from collections import defaultdict

from chain_planner import get_pickup_hint
from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class ValidActionsSection(PromptSection):
    """Renders valid actions as a simple table format."""

    def __init__(self, instructions: str | None = None):
        super().__init__()
        self.instructions = instructions or self._default_instructions()

    def _default_instructions(self) -> str:
        return """Pick ONE action and ONE target. Reply with JSON: {"action":"...","target":"...","reason":"..."}"""

    def _extract_distance(self, target: str) -> float:
        """Extract distance in meters from target string like 'flint (3.2m)'."""
        match = re.search(r"\((\d+\.?\d*)m\)", target)
        if match:
            return float(match.group(1))
        return float("inf")  # No distance = put at end

    def _extract_item_name(self, target: str) -> str:
        """Extract base item name from target string like 'flint (3.2m) [CLOSEST]' -> 'flint'."""
        # Remove distance suffix and tags
        name = re.sub(r"\s*\([\d.]+m\)", "", target)
        name = re.sub(r"\s*\[(?:CLOSEST|FARTHEST)\]", "", name)
        return name.strip().lower()

    def render(self, ctx: PromptContext) -> str:
        valid_actions = ctx.current_turn_actions

        if not valid_actions:
            actions_text = "  explore: N, S, E, W, NE, NW, SE, SW"
        else:
            # Group actions by action name
            grouped: dict[str, list[str | None]] = defaultdict(list)
            for opt in valid_actions:
                grouped[opt.action].append(opt.target)

            # Format as simple "action: target1, target2, ..." lines
            action_lines = []
            for action_name, targets in grouped.items():
                valid_targets = [t for t in targets if t is not None]
                if not valid_targets:
                    continue

                # Only sort and tag if targets have distances (physical items/entities)
                has_distances = any(
                    self._extract_distance(t) != float("inf") for t in valid_targets
                )

                if has_distances:
                    # Sort by distance (closest first)
                    valid_targets.sort(key=self._extract_distance)

                    # Add tags to first and last
                    tagged_targets = []
                    for i, target in enumerate(valid_targets):
                        if len(valid_targets) > 1:
                            if i == 0:
                                tagged_targets.append(f"{target} [CLOSEST]")
                            elif i == len(valid_targets) - 1:
                                tagged_targets.append(f"{target} [FARTHEST]")
                            else:
                                tagged_targets.append(target)
                        else:
                            tagged_targets.append(target)
                    valid_targets = tagged_targets

                    # Add strategic hints for critical materials (pick_up_item only)
                    if action_name == "pick_up_item":
                        inventory = ctx.state.get_inventory_dict()
                        hinted_targets = []
                        for target in valid_targets:
                            item_name = self._extract_item_name(target)
                            chain = get_pickup_hint(item_name, inventory)
                            hinted_targets.append(target + chain)
                        valid_targets = hinted_targets

                targets_str = ", ".join(valid_targets)
                action_lines.append(f"  {action_name}: {targets_str}")

            actions_text = "\n".join(action_lines)

        return f"""{self.instructions}
[ACTIONS]
{actions_text}
[/ACTIONS]"""
