"""Regression tests for inventory rendering in prompts."""

from models.state import GameState
from prompt import build_prompt


def test_prompt_inventory_preserves_stack_counts():
    state = GameState(
        day=0,
        time_of_day=0.0,
        phase="day",
        season="spring",
        temperature=12.0,
        health=150,
        hunger=67,
        sanity=170,
        inventory=["twigs x7"],
        equipped=None,
    )

    prompt = build_prompt(state=state, memory=[], goals="")

    assert "[INVENTORY]" in prompt
    assert "twigs x7" in prompt
    assert "\n  twigs\n[/INVENTORY]" not in prompt