"""
state.py — Pydantic models for game state data.

Defines the schema for game state snapshots exported from Don't Starve.
"""

from pydantic import BaseModel, Field


class Position(BaseModel):
    """2D position in the game world."""

    x: float
    z: float


class NearbyEntity(BaseModel):
    """An entity near the player."""

    name: str
    type: str
    distance: float


class Threat(BaseModel):
    """A hostile entity threatening the player."""

    name: str
    distance: float


class ActionLogEntry(BaseModel):
    """A logged action result from the game."""

    result: str  # "success", "failed", etc.
    action: str
    reason: str | None = None


class MemoryLogEntry(BaseModel):
    """A memory/event log entry."""

    source: str  # "damage", "llm_reason", "event", etc.
    text: str


class GameState(BaseModel):
    """Complete game state snapshot from Don't Starve.

    This model validates and provides type-safe access to all game state fields
    exported by the Lua components.
    """

    # Time and world
    day: int = Field(default=1, description="Current day number")
    time_of_day: float = Field(default=0.0, description="Time within current day (0-1)")
    phase: str = Field(default="day", description="Current phase: day/dusk/night")
    season: str = Field(default="autumn", description="Current season")
    is_raining: bool = Field(default=False, description="Whether it's raining")
    temperature: float | None = Field(
        default=None, description="Current temperature in Celsius"
    )

    # Player vitals
    health: float = Field(description="Player current health")
    hunger: float = Field(description="Player current hunger")
    sanity: float = Field(description="Player current sanity")

    # Inventory and equipment
    inventory: list[str] = Field(
        default_factory=list, description="Item list with counts"
    )
    equipped: str | None = Field(default=None, description="Currently equipped item")

    # Current action (from behavior tree)
    current_action: str | None = Field(default=None, description="Active action name")
    action_target: str | None = Field(
        default=None, description="Target of current action"
    )

    # Position
    position: Position | None = Field(default=None, description="Player position")

    # World perception
    nearby_entities: list[NearbyEntity] = Field(
        default_factory=list, description="Entities within perception radius"
    )
    threats: list[Threat] = Field(
        default_factory=list, description="Hostile entities nearby"
    )

    # Logs (accumulator buffers cleared each export)
    speech_log: list[str] = Field(
        default_factory=list, description="Recent speech bubbles"
    )
    action_log: list[ActionLogEntry] = Field(
        default_factory=list, description="Recent action results"
    )
    memory_log: list[MemoryLogEntry] = Field(
        default_factory=list, description="General event log"
    )

    @property
    def is_critical_health(self) -> bool:
        """Health is critically low (< 50)."""
        return self.health < 50

    @property
    def is_critical_hunger(self) -> bool:
        """Hunger is critically low (< 50)."""
        return self.hunger < 50

    @property
    def is_critical_sanity(self) -> bool:
        """Sanity is critically low (< 50)."""
        return self.sanity < 50

    @property
    def is_night(self) -> bool:
        """Currently nighttime."""
        return self.phase == "night"

    @property
    def is_dusk(self) -> bool:
        """Currently dusk."""
        return self.phase == "dusk"

    @property
    def has_threats(self) -> bool:
        """Any threats nearby."""
        return len(self.threats) > 0

    def get_inventory_dict(self) -> dict[str, int]:
        """
        Parse inventory list into item counts.

        Converts ["log x20", "axe"] -> {"log": 20, "axe": 1}
        """
        result: dict[str, int] = {}
        for item in self.inventory:
            if " x" in item:
                name, _, count = item.rpartition(" x")
                result[name.strip()] = int(count)
            else:
                result[item.strip()] = 1
        return result

    def has_item(self, item_name: str) -> bool:
        """Check if inventory contains an item."""
        inv_dict = self.get_inventory_dict()
        return item_name in inv_dict

    def get_item_count(self, item_name: str) -> int:
        """Get count of specific item in inventory."""
        inv_dict = self.get_inventory_dict()
        return inv_dict.get(item_name, 0)
