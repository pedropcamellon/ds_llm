"""
concrete_action_builder.py — ConcreteActionBuilder.

Single responsibility: translate a live game state + inventory into a
prioritised list of *specific* action options for the LLM.

Depends on PrereqFilter for prerequisite checking and on entity_sets for
prefab classification. Has no knowledge of prompts or HTTP clients.
"""

from entity_sets import (
    EDIBLE_PREFABS,
    HARVESTABLE_ENTITIES,
    HARVEST_REQUIRES_TOOL,
    HOSTILE_ENTITIES,
    HOSTILE_TYPES,
    PICKUP_PREFABS,
)
from models import ActionOption, GameState
from prereq_filter import PrereqFilter


class ConcreteActionBuilder:
    """Generates a labelled, ordered action list from inventory + game state."""

    def __init__(self, prereq_filter: PrereqFilter | None = None) -> None:
        self._filter = prereq_filter or PrereqFilter()

    def build(self, inv: dict[str, int], state: GameState) -> list[ActionOption]:
        """Return concrete, specific action options the LLM can pick from.

        Order (most specific / high priority first):
          1. Craft actions (ingredient costs shown inline)
          2. Tool-gated actions (chop_tree, mine_rock)
          3. pick_up_item with target for nearby loose items
          4. gather_resource with target for nearby harvestable entities
          5. eat_food with target per edible in inventory
          6. attack_enemy / run_from_enemy for active threats
          7. explore / idle (always last)
        """
        from action_specs import normalize_inv  # local to avoid circular at module load

        inv_norm = normalize_inv(inv)
        base_valid = set(self._filter.get_valid_actions(inv))
        actions: list[ActionOption] = []

        # 1. Craft actions — only those whose prereqs are met
        for action in sorted(base_valid):
            if action.startswith("craft_item:"):
                item_name = action.replace("craft_item:", "")
                spec = self._filter.specs[action]
                if spec.requires:
                    cost = "+".join(f"{k}x{v}" for k, v in spec.requires.items())
                    actions.append(
                        ActionOption(
                            action="craft_item", target=f"{item_name} ({cost})"
                        )
                    )
                else:
                    actions.append(ActionOption(action="craft_item", target=item_name))

        # 2. Tool-gated actions
        if "chop_tree" in base_valid:
            actions.append(ActionOption(action="chop_tree"))
        if "mine_rock" in base_valid:
            actions.append(ActionOption(action="mine_rock"))

        # Scan up to 30 nearby entities (Lua exports many; first 10 are often
        # ambient: snow, rain, flowers, flies which all come before resources)
        nearby = state.nearby_entities or []

        # 3. Pick-up specific ground items from nearby loose entities.
        # Track which resources are already available as loose pickups so step 4
        # can skip offering gather_resource for the same yield (redundant).
        pickup_resources: set[str] = set()
        seen_pickups: set[str] = set()
        for entity in nearby[:30]:
            name = (entity.name or "").lower()
            etype = (entity.type or "").lower()
            # Never treat a harvestable plant as a ground item — it yields
            # resources only via gather_resource (step 4), not pick_up_item.
            if etype == "harvestable":
                continue
            is_item_type = etype in ("item", "resource")
            if (name in PICKUP_PREFABS or is_item_type) and name in PICKUP_PREFABS:
                if name not in seen_pickups:
                    seen_pickups.add(name)
                    dist = entity.distance
                    actions.append(
                        ActionOption(action="pick_up_item", target=f"{name} ({dist}m)")
                    )
                pickup_resources.add(name)

        # 4. Gather specific resources from nearby harvestable entities.
        # Skip yields already covered by a loose pickup (e.g. don't offer
        # gather_resource:twigs when pick_up_item:twigs is already listed).
        seen_yields: set[str] = set()
        for entity in nearby[:30]:
            name = (entity.name or "").lower()
            etype = (entity.type or "").lower()
            if name in HOSTILE_ENTITIES or etype in HOSTILE_TYPES:
                continue
            if name in PICKUP_PREFABS:
                continue
            # Accept both explicit harvestable type AND known harvestable names
            is_harvestable = etype == "harvestable" or name in HARVESTABLE_ENTITIES
            if not is_harvestable:
                continue
            # Skip if a specific tool is required and not present
            required_tool = HARVEST_REQUIRES_TOOL.get(name)
            if required_tool and inv_norm.get(required_tool, 0) < 1:
                continue
            yielded = HARVESTABLE_ENTITIES.get(name, name)
            if yielded in pickup_resources:
                continue  # loose item already on the ground — no need to harvest
            if yielded not in seen_yields:
                seen_yields.add(yielded)
                dist = entity.distance or "?"
                actions.append(
                    ActionOption(
                        action="gather_resource", target=f"{yielded} ({dist}m)"
                    )
                )

        # Fallback gather when nothing specific is visible
        if not seen_yields:
            actions.append(
                ActionOption(
                    action="gather_resource", target="find something to harvest"
                )
            )

        # 5. Eat specific food from inventory
        edibles = sorted(
            item for item in inv_norm if item in EDIBLE_PREFABS and inv_norm[item] > 0
        )
        for food in edibles:
            actions.append(
                ActionOption(
                    action="eat_food", target=f"{food} (have {inv_norm[food]})"
                )
            )

        # 6. Threats → attack or run
        threats = state.threats or []
        for threat in threats[:2]:
            tname = (threat.name or "unknown").lower()
            tdist = threat.distance or "?"
            actions.append(
                ActionOption(action="attack_enemy", target=f"{tname} ({tdist}m)")
            )
        if threats:
            actions.append(ActionOption(action="run_from_enemy"))

        # 7. Exploration fallback (always available)
        for direction in ["N", "S", "E", "W", "NE", "NW", "SE", "SW"]:
            actions.append(ActionOption(action="explore", target=direction))

        return actions
