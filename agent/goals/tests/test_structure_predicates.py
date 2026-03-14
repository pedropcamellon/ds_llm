"""Test structure predicates — has_structure for nearby entities."""

from models.state import GameState
from goals.predicates import has_structure


def test_has_structure_when_nearby():
    """has_structure("science_machine") returns True when in nearby_entities."""
    state = GameState(
        health=100,
        hunger=100,
        sanity=200,
        phase="day",
        season="autumn",
        day=1,
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 3},
            {"name": "campfire", "type": "structure", "distance": 5}
        ]
    )
    assert has_structure("science_machine")(state) is True


def test_has_structure_when_not_nearby():
    """has_structure("alchemy_engine") returns False when not in nearby_entities."""
    state = GameState(
        health=100,
        hunger=100,
        sanity=200,
        phase="day",
        season="autumn",
        day=1,
        nearby_entities=[
            {"name": "science_machine", "type": "structure", "distance": 3},
            {"name": "campfire", "type": "structure", "distance": 5}
        ]
    )
    assert has_structure("alchemy_engine")(state) is False


def test_has_structure_when_empty_list():
    """has_structure returns False when nearby_entities is []."""
    state = GameState(
        health=100,
        hunger=100,
        sanity=200,
        phase="day",
        season="autumn",
        day=1,
        nearby_entities=[]
    )
    assert has_structure("campfire")(state) is False
