"""
inventory.py — Inventory section.
"""

from prompt.sections.base import PromptSection
from prompt.sections.context import PromptContext


class InventorySection(PromptSection):
    """Renders current inventory items."""

    def render(self, ctx: PromptContext) -> str:
        inv = ctx.state.get_inventory_dict()

        inv_line = (
            ", ".join(
                f"{name} x{count}" if count > 1 else name
                for name, count in sorted(inv.items())
            )
            or "empty"
        )

        return f"""[INVENTORY]
  {inv_line}
[/INVENTORY]"""
