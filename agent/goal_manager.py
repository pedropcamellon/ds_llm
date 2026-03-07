"""
goal_manager.py — Derives long-term and short-term survival goals from game state.

Long-term goals are season-based (survive winter, prepare for summer, etc.).
Short-term goals are urgent situational rules (health critical, night approaching,
threat nearby, etc.) and override the long-term goal when present.

The GoalManager does NOT filter actions — that's GoalPlanner's job.
It produces:
  - A human-readable goals block for the prompt [GOALS]
  - A preferred_actions list to reorder valid_actions (most relevant first)
"""

from dataclasses import dataclass, field
from enum import Enum

from models import GameState

class StateFieldError(ValueError):
    """Raised when a required game-state field is missing or None.

    Catching this in the agent loop means the Lua exporter is broken or the
    state file is stale/corrupt.  The agent should stop issuing actions and
    ask the player to pause rather than silently acting on wrong values.
    """


def _require_field(state: GameState, key: str, cast: type = str):
    """Extract a required state field, raising StateFieldError if absent.

    Never use defaults for safety-critical fields — that
    silently swallows None/0/empty-string and causes wrong decisions.
    """
    value = getattr(state, key, None)
    if value is None:
        raise StateFieldError(
            f"[StateFieldError] Required field '{key}' is None in game_state — "
            "Lua exporter may be broken. PAUSE THE GAME and check log.txt."
        )
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise StateFieldError(
            f"[StateFieldError] Field '{key}' cannot be cast to {cast.__name__} "
            f"(got {value!r}). PAUSE THE GAME and check log.txt."
        ) from exc


class Urgency(Enum):
    CRITICAL = 0
    URGENT = 1
    MODERATE = 2
    LOW = 3


@dataclass
class ShortTermGoal:
    urgency: Urgency
    description: str
    preferred_actions: list[str]
    reason: str


@dataclass
class LongTermGoal:
    season: str
    description: str
    focus_actions: list[str] = field(default_factory=list)


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

    _LONG_TERM: dict[str, LongTermGoal] = {
        "autumn": LongTermGoal(
            season="autumn",
            description=(
                "Gather food, logs, flint. Build a firepit."
                " Craft warm clothes before winter."
            ),
            focus_actions=[
                "gather_resource",
                "chop_tree",
                "craft_item:campfire",
                "craft_item:axe",
            ],
        ),
        "winter": LongTermGoal(
            season="winter",
            description=(
                "Nights are long, food is scarce, cold is deadly."
                " Stay near fire. Ration food. Survive until spring."
            ),
            focus_actions=[
                "craft_item:torch",
                "craft_item:campfire",
                "gather_resource",
                "eat_food",
            ],
        ),
        "spring": LongTermGoal(
            season="spring",
            description=(
                "Recover sanity. Gather regrown resources."
                " Watch for frogs. Prepare for summer heat."
            ),
            focus_actions=["gather_resource", "explore"],
        ),
        "summer": LongTermGoal(
            season="summer",
            description=(
                "Overheating is fatal. Avoid open ground at noon."
                " Stay near cold sources. Manage food and sanity."
            ),
            focus_actions=["gather_resource", "eat_food", "explore"],
        ),
    }

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_long_term_goal(self, state: GameState) -> LongTermGoal:
        """Return the season-appropriate long-term goal."""
        season = _require_field(state, "season", str).lower()
        return self._LONG_TERM.get(season, self._LONG_TERM["autumn"])

    def get_short_term_goal(
        self, state: GameState, inv: dict[str, int]
    ) -> ShortTermGoal | None:
        """Return the most urgent short-term goal, or None if stable.

        Raises StateFieldError if any required stat field is missing — callers
        must catch this and emit an idle/pause action rather than proceeding.
        """
        health = _require_field(state, "health", float)
        hunger = _require_field(state, "hunger", float)
        sanity = _require_field(state, "sanity", float)
        phase = _require_field(state, "phase", str).lower()
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
        """Return the formatted [GOALS] block content (no XML tags)."""
        ltg = self.get_long_term_goal(state)
        stg = self.get_short_term_goal(state, inv)

        lines: list[str] = [
            f"Long-term ({ltg.season.capitalize()}): {ltg.description}",
        ]
        if stg:
            lines.append(f"Short-term [{stg.urgency.name}]: {stg.description}")
        else:
            lines.append("Short-term: Stable — gather resources, build, explore.")

        return "\n  ".join(lines)

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

        # Build actionable options based on what the player can actually craft
        options: list[str] = []
        can_torch = inv.get("twigs", 0) >= 2 and inv.get("cutgrass", 0) >= 2
        can_campfire = inv.get("log", 0) >= 2 and inv.get("cutgrass", 0) >= 3

        if can_torch:
            options.append("craft_item:torch (twigsx2+cutgrassx2 - ready!)")
        if can_campfire:
            options.append("craft_item:campfire (logx2+cutgrassx3 - ready!)")

        if not options:
            # Cheapest path is a torch; tell the player what to gather
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
