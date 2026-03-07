"""
tools.py — Tool prerequisites and craftability section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext

# Crafting recipes
RECIPES: dict[str, dict[str, int]] = {
    "axe": {"twig": 1, "flint": 1},
    "pickaxe": {"twig": 2, "flint": 2},
    "campfire": {"log": 2, "cutgrass": 2},
    "torch": {"twig": 2, "cutgrass": 2},
}


class ToolsSection(PromptSection):
    """Renders tool status and craftability info."""

    def render(self, ctx: PromptContext) -> str:
        inv = ctx.state.get_inventory_dict()

        lines = []

        # Key tools
        has_axe = "axe" in inv
        has_pickaxe = "pickaxe" in inv

        lines.append(
            f"  axe: {'have it' if has_axe else 'missing — craft_item:axe needs 1 twig + 1 flint'}"
        )
        lines.append(
            f"  pickaxe: {'have it' if has_pickaxe else 'missing — craft_item:pickaxe needs 2 twig + 2 flint'}"
        )

        # Craftable items
        craftable = [
            name
            for name, recipe in RECIPES.items()
            if all(inv.get(ing, 0) >= qty for ing, qty in recipe.items())
        ]
        if craftable:
            lines.append(f"  Can craft now: {', '.join(craftable)}")

        # Action gating
        if not has_axe:
            lines.append("  chop_tree requires an axe — craft or find one first")
        if not has_pickaxe:
            lines.append("  mine_rock requires a pickaxe — craft or find one first")

        return f"""[TOOLS]
{chr(10).join(lines)}
[/TOOLS]"""
