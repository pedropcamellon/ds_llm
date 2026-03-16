"""
goals/manager.py — GoalManager: derives context-aware goals from game state + inventory.

The GoalManager does NOT filter actions — that is GoalPlanner's job.
It produces:
  - A human-readable goals block for the LLM prompt  [format_for_prompt]
  - A terminal TUI block for CLI debug output         [format_for_cli]
  - Preferred-action hints to reorder valid_actions   [ShortTermGoal.preferred_actions]
"""

import textwrap

from models import GameState
from state_manager import require_field
from world_calendar import Season

from goals.models import LongTermGoal, MidTermGoal, ShortTermGoal, Urgency
from goals.predicates import season_is, has_structure

# Prefabs that count as a "light source" for the night check
_FIRE_PREFABS = frozenset(
    {
        "campfire",
        "campfire_small",
        "firepit",
        "torch",
        "minerhat",
        "lantern",
        "nightlight",
        "winterometer",  # not actually light, but fine to ignore
    }
)

class GoalManager:
    """Derives context-aware goals from game state + inventory."""

    _LONG_TERM: dict[Season, LongTermGoal] = {
        Season.AUTUMN: LongTermGoal(
            season="autumn",
            description=(
                "Mild weather. Medium day length. Resources abundant. "
                "Winter approaches — will bring freezing temps and food scarcity."
            ),
            focus_actions=[
                "gather_resource",
                "chop_tree",
                "craft_item",
                "build_structure",
            ],
            goal_check=season_is("winter"),  # Complete when winter arrives
        ),
        Season.WINTER: LongTermGoal(
            season="winter",
            description=(
                "Freezing temperatures. Long nights, short days. "
                "Food scarce. Cold is lethal. Spring will bring relief."
            ),
            focus_actions=["gather_resource", "craft_item", "eat_food"],
            goal_check=season_is("spring"),  # Complete when spring arrives
        ),
        Season.SPRING: LongTermGoal(
            season="spring",
            description=(
                "Moderate weather. Resources regrow. Rain common. Frogs spawn. "
                "Summer heat approaches — will bring overheating risk."
            ),
            focus_actions=[
                "gather_resource",
                "explore",
                "build_structure",
                "craft_item",
            ],
            goal_check=season_is("summer"),  # Complete when summer arrives
        ),
        Season.SUMMER: LongTermGoal(
            season="summer",
            description=(
                "Scorching heat. Overheating and wildfires common. "
                "Stay cool or die. Autumn relief is coming."
            ),
            focus_actions=["gather_resource", "craft_item", "explore"],
            goal_check=season_is("autumn"),  # Complete when autumn arrives
        ),
    }

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_long_term_goal(self, state: GameState) -> LongTermGoal:
        """Return the season-appropriate long-term goal."""
        season_str = require_field(state, "season", str).lower()
        season = Season(season_str)
        return self._LONG_TERM.get(season, self._LONG_TERM[Season.AUTUMN])

    def get_mid_term_goals(
        self, state: GameState, inv: dict[str, int], limit: int = 3
    ) -> list[MidTermGoal]:
        """Return 2-3 mid-term goal options for LLM to choose from.

        Generates context-appropriate tactical options based on:
        - Missing structures (no science machine → offer "Build base")
        - Low resources (food < 10 → offer "Stockpile food")
        - Seasonal prep (autumn → offer "Prepare for winter")
        - Exploration (always offered as universal option)

        Args:
            state: Current game state
            inv: Inventory counts (e.g., {"log": 5, "cooked_meat": 2})
            limit: Maximum number of goals to return (default: 3)

        Returns:
            List of 2-3 incomplete mid-term goals with predicates
        """
        season_str = require_field(state, "season", str).lower()
        season = Season(season_str)
        goals: list[MidTermGoal] = []

        # 1. Base building (if no science machine)
        if not has_structure("science_machine")(state):
            goals.append(
                MidTermGoal(
                    day_range="",  # Not day-specific
                    description="Build base with science machine for advanced crafting",
                    focus_actions=["gather_resource", "craft_item", "explore_map"],
                    reason="missing_science_machine",
                    goal_check=has_structure("science_machine"),
                )
            )

        # 2. Seasonal preparation
        if season == Season.AUTUMN:
            # Prepare for winter
            goals.append(
                MidTermGoal(
                    day_range="",
                    description="Prepare for winter (craft thermal stone and gather fuel)",
                    focus_actions=["gather_resource", "craft_item"],
                    reason="winter_approaching",
                    goal_check=lambda s: (
                        s.season == "winter"
                    ),  # Complete when winter arrives
                )
            )

        # 3. Food stockpiling (if low food reserves)
        food_count = sum(
            count
            for item, count in inv.items()
            if any(
                food_type in item.lower()
                for food_type in ["meat", "berry", "carrot", "fish"]
            )
        )
        if food_count < 10:
            goals.append(
                MidTermGoal(
                    day_range="",
                    description="Stockpile food reserves for survival",
                    focus_actions=["gather_resource", "hunt_mob", "cook_food"],
                    reason="low_food_reserves",
                    goal_check=lambda s: False,  # Always incomplete (food is ongoing)
                )
            )

        # 4. Exploration (always offered as universal option)
        goals.append(
            MidTermGoal(
                day_range="",
                description="Explore unmapped areas to find resources and biomes",
                focus_actions=["explore_map"],
                reason="universal_option",
                goal_check=lambda s: (
                    False
                ),  # Always incomplete (exploration is ongoing)
            )
        )

        # Filter to incomplete goals only
        incomplete_goals = []
        for g in goals:
            if g.goal_check and g.goal_check(state):
                continue

            incomplete_goals.append(g)

        # Limit to requested number (default 3)
        return incomplete_goals[:limit]

    def get_short_term_goal(
        self, state: GameState, inv: dict[str, int]
    ) -> ShortTermGoal | None:
        """Return the most urgent short-term goal, or None if stable.

        Raises StateFieldError if any required stat field is missing — callers
        must catch this and emit an idle/pause action rather than proceeding.
        """
        health = require_field(state, "health", float)
        hunger = require_field(state, "hunger", float)
        sanity = require_field(state, "sanity", float)
        phase = require_field(state, "phase", str).lower()
        # temperature is optional (thermometer is a crafted item; may not exist yet)
        temperature = state.temperature
        threats = state.threats or []

        # ── CRITICAL ──────────────────────────────────────────────────
        if health < 20:
            return ShortTermGoal(
                urgency=Urgency.CRITICAL,
                description="Health critical! Eat food or run immediately.",
                preferred_actions=["eat_food", "run_from_enemy"],
                reason="health < 20",
            )

        if threats:
            name = threats[0].name or "unknown"
            dist = threats[0].distance or "?"
            return ShortTermGoal(
                urgency=Urgency.CRITICAL,
                description=f"Threat: {name} at {dist}m — run or fight.",
                preferred_actions=["run_from_enemy", "attack_enemy"],
                reason=f"threat: {name}",
            )

        # ── URGENT ────────────────────────────────────────────────────
        if phase in ("dusk", "night"):
            return self._fire_goal(state, inv, phase)

        if hunger < 25:
            return ShortTermGoal(
                urgency=Urgency.URGENT,
                description="Starving! Eat or find food now.",
                preferred_actions=["eat_food", "gather_resource"],
                reason="hunger < 25",
            )

        if temperature is not None and float(temperature) < 0:
            return ShortTermGoal(
                urgency=Urgency.URGENT,
                description=f"Freezing ({temperature}C)! Light a fire or find warmth.",
                preferred_actions=[
                    "craft_item:campfire",
                    "craft_item:torch",
                    "gather_resource",
                ],
                reason=f"temperature={temperature}",
            )

        # ── MODERATE ──────────────────────────────────────────────────
        if sanity < 60:  # out of 200
            return ShortTermGoal(
                urgency=Urgency.MODERATE,
                description="Sanity low. Pick flowers, stand near fire, or avoid darkness.",
                preferred_actions=["gather_resource", "explore", "idle"],
                reason="sanity < 60/200",
            )

        if hunger < 50:  # out of 150
            return ShortTermGoal(
                urgency=Urgency.MODERATE,
                description="Getting hungry. Find berries, seeds, or hunt.",
                preferred_actions=["gather_resource", "eat_food", "explore"],
                reason="hunger < 50/150",
            )

        return None

    def format_for_prompt(self, state: GameState, inv: dict[str, int]) -> str:
        """Return the formatted [GOALS] block content (no XML tags).

        Completed goals (where goal_check returns True) are omitted entirely.
        """
        ltg = self.get_long_term_goal(state)
        mtgs = self.get_mid_term_goals(state, inv)  # Returns list of 2-3 options
        stg = self.get_short_term_goal(state, inv)

        lines: list[str] = []

        # Only show long-term if not complete
        if not (ltg.goal_check and ltg.goal_check(state)):
            lines.append(f"Long-term ({ltg.season.capitalize()}): {ltg.description}")

        # Show mid-term goal options (2-3 tactical choices)
        if mtgs:
            lines.append("Mid-term options (choose one):")
            for i, mtg in enumerate(mtgs, 1):
                lines.append(f"  {i}. {mtg.description}")
        else:
            lines.append("Mid-term: No tactical goals available.")

        # Only show short-term if exists and not complete
        if stg:
            if not (stg.goal_check and stg.goal_check(state)):
                lines.append(f"Short-term [{stg.urgency.name}]: {stg.description}")
        else:
            lines.append("Short-term: Stable — no urgent needs.")

        return "\n  ".join(lines)

    def format_for_cli(
        self, state: GameState, inv: dict[str, int], width: int = 96
    ) -> str:
        """Return a terminal-friendly TUI block for goals output.

        This format is optimized for logging in CLI mode with clear spacing,
        wrapped text, and stable section labels.
        """
        ltg = self.get_long_term_goal(state)
        mtgs = self.get_mid_term_goals(state, inv)  # Returns list of 2-3 options
        stg = self.get_short_term_goal(state, inv)

        inner = max(width - 4, 40)

        def _wrap(line: str, indent: str = "") -> list[str]:
            return textwrap.wrap(
                line,
                width=inner,
                initial_indent=indent,
                subsequent_indent=indent,
            ) or [indent]

        rows: list[str] = []
        rows.append("GOALS")
        rows.append("")

        rows.append(f"[LONG-TERM] {ltg.season.capitalize()}")
        rows.extend(_wrap(ltg.description, indent="  "))
        rows.append("")

        rows.append("[MID-TERM] Options")
        if mtgs:
            for i, mtg in enumerate(mtgs, 1):
                rows.extend(_wrap(f"{i}. {mtg.description}", indent="  "))
        else:
            rows.extend(_wrap("No tactical goals.", indent="  "))
        rows.append("")

        if stg:
            rows.append(f"[SHORT-TERM] {stg.urgency.name}")
            rows.extend(_wrap(stg.description, indent="  "))
        else:
            rows.append("[SHORT-TERM] STABLE")
            rows.extend(_wrap("No urgent needs.", indent="  "))

        border = "+" + "-" * (inner + 2) + "+"
        boxed = [border]
        for row in rows:
            boxed.append(f"| {row.ljust(inner)} |")
        boxed.append(border)
        return "\n".join(boxed)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fire_nearby(self, state: GameState) -> bool:
        return any(e.name in _FIRE_PREFABS for e in (state.nearby_entities or []))

    def _fire_goal(
        self, state: GameState, inv: dict[str, int], phase: str
    ) -> ShortTermGoal:
        if self._fire_nearby(state):
            return ShortTermGoal(
                urgency=Urgency.LOW,
                description=f"It's {phase} but there's a fire nearby — stay close.",
                preferred_actions=["idle", "eat_food", "gather_resource"],
                reason=f"phase={phase}, fire nearby",
            )

        options: list[str] = []
        can_torch = inv.get("twigs", 0) >= 2 and inv.get("cutgrass", 0) >= 2
        can_campfire = inv.get("log", 0) >= 2 and inv.get("cutgrass", 0) >= 3

        if can_torch:
            options.append("craft_item:torch")
        if can_campfire:
            options.append("craft_item:campfire")

        if not options:
            twigs_have = inv.get("twigs", 0)
            grass_have = inv.get("cutgrass", 0)
            need_parts: list[str] = []
            if twigs_have < 2:
                need_parts.append(f"twigs (have {twigs_have}, need 2)")
            if grass_have < 2:
                need_parts.append(f"cutgrass (have {grass_have}, need 2)")
            gather_hint = " + ".join(need_parts) if need_parts else "twigs+cutgrass"
            options.append(f"Gather {gather_hint} -> then craft_item:torch")

        desc = f"Night! No fire. {' OR '.join(options)}"
        return ShortTermGoal(
            urgency=Urgency.URGENT,
            description=desc,
            preferred_actions=[
                "craft_item:torch",
                "craft_item:campfire",
                "gather_resource",
            ],
            reason=f"phase={phase}, no fire",
        )
