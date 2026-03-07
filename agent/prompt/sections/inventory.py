"""
inventory.py — Inventory section with tool annotations.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext

# Tools and what they enable
TOOL_ENABLES: dict[str, str] = {
    "axe": "chop_tree",
    "pickaxe": "mine_rock",
    "shovel": "dig",
    "hammer": "demolish",
    "torch": "light",
    "lantern": "light",
}

# Tool recipes for "missing" hints
TOOL_RECIPES: dict[str, str] = {
    "axe": "1 twig + 1 flint",
    "pickaxe": "2 twig + 2 flint",
    "shovel": "2 twig + 2 flint",
    "hammer": "3 twig + 3 rocks + 2 cutgrass",
    "torch": "2 twig + 2 cutgrass",
}


class InventorySection(PromptSection):
    """Renders inventory with tool tags."""

    def render(self, ctx: PromptContext) -> str:
        inv = ctx.state.get_inventory_dict()

        # Format items with tool annotations
        items = []
        for name, count in sorted(inv.items()):
            if name in TOOL_ENABLES:
                tag = f" (enables {TOOL_ENABLES[name]})"
            else:
                tag = ""
            
            if count > 1:
                items.append(f"{name} x{count}{tag}")
            else:
                items.append(f"{name}{tag}")

        inv_line = ", ".join(items) or "empty"

        return f"""[INVENTORY]
  {inv_line}
[/INVENTORY]"""
