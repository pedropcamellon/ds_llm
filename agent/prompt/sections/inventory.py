"""
inventory.py — Inventory section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class InventorySection(PromptSection):
    """Renders inventory items."""

    def render(self, ctx: PromptContext) -> str:
        inv = ctx.state.get_inventory_dict()

        # Format items (plain list, no tags - strategic info moved to actions)
        items = []
        for name, count in sorted(inv.items()):
            if count > 1:
                items.append(f"{name} x{count}")
            else:
                items.append(name)

        inv_line = ", ".join(items) or "empty"

        return f"""[INVENTORY]
  {inv_line}
[/INVENTORY]"""
