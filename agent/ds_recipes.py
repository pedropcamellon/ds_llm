"""
ds_recipes.py — All Don't Starve vanilla recipes, parsed from recipes.lua.

This file is auto-generated for agent reference and planning. Each recipe is a dict:
{
    "name": "axe",
    "ingredients": {"twigs": 1, "flint": 1},
    "tab": "TOOLS",
    "tech": "NONE",
    "placer": None,
    "notes": ""
}
"""

RECIPES = [
    # LIGHT
    {
        "name": "campfire",
        "ingredients": {"cutgrass": 3, "log": 2},
        "tab": "LIGHT",
        "tech": "NONE",
        "placer": "campfire_placer",
        "notes": "",
    },
    {
        "name": "firepit",
        "ingredients": {"log": 2, "rocks": 12},
        "tab": "LIGHT",
        "tech": "NONE",
        "placer": "firepit_placer",
        "notes": "",
    },
    {
        "name": "torch",
        "ingredients": {"cutgrass": 2, "twigs": 2},
        "tab": "LIGHT",
        "tech": "NONE",
        "placer": None,
        "notes": "",
    },
    {
        "name": "minerhat",
        "ingredients": {"strawhat": 1, "goldnugget": 1, "fireflies": 1},
        "tab": "LIGHT",
        "tech": "SCIENCE_TWO",
        "placer": None,
        "notes": "",
    },
    {
        "name": "pumpkin_lantern",
        "ingredients": {"pumpkin": 1, "fireflies": 1},
        "tab": "LIGHT",
        "tech": "SCIENCE_TWO",
        "placer": None,
        "notes": "",
    },
    {
        "name": "lantern",
        "ingredients": {"twigs": 3, "rope": 2, "lightbulb": 2},
        "tab": "LIGHT",
        "tech": "SCIENCE_TWO",
        "placer": None,
        "notes": "",
    },
    # STRUCTURES
    {
        "name": "treasurechest",
        "ingredients": {"boards": 3},
        "tab": "TOWN",
        "tech": "SCIENCE_ONE",
        "placer": "treasurechest_placer",
        "notes": "",
    },
    {
        "name": "homesign",
        "ingredients": {"boards": 1},
        "tab": "TOWN",
        "tech": "SCIENCE_ONE",
        "placer": "homesign_placer",
        "notes": "",
    },
    {
        "name": "minisign_item",
        "ingredients": {"boards": 1},
        "tab": "TOWN",
        "tech": "SCIENCE_ONE",
        "placer": None,
        "notes": "stacksize=4",
    },
    {
        "name": "fence_gate_item",
        "ingredients": {"boards": 2, "rope": 1},
        "tab": "TOWN",
        "tech": "SCIENCE_TWO",
        "placer": None,
        "notes": "stacksize=1",
    },
    {
        "name": "fence_item",
        "ingredients": {"twigs": 3, "rope": 1},
        "tab": "TOWN",
        "tech": "SCIENCE_ONE",
        "placer": None,
        "notes": "stacksize=6",
    },
    {
        "name": "wall_hay_item",
        "ingredients": {"cutgrass": 4, "twigs": 2},
        "tab": "TOWN",
        "tech": "SCIENCE_ONE",
        "placer": None,
        "notes": "stacksize=4",
    },
    {
        "name": "wall_wood_item",
        "ingredients": {"boards": 2, "rope": 1},
        "tab": "TOWN",
        "tech": "SCIENCE_ONE",
        "placer": None,
        "notes": "stacksize=8",
    },
    {
        "name": "wall_stone_item",
        "ingredients": {"cutstone": 2},
        "tab": "TOWN",
        "tech": "SCIENCE_TWO",
        "placer": None,
        "notes": "stacksize=6",
    },
    {
        "name": "pighouse",
        "ingredients": {"boards": 4, "cutstone": 3, "pigskin": 4},
        "tab": "TOWN",
        "tech": "SCIENCE_TWO",
        "placer": "pighouse_placer",
        "notes": "",
    },
    {
        "name": "rabbithouse",
        "ingredients": {"boards": 4, "carrot": 10, "manrabbit_tail": 4},
        "tab": "TOWN",
        "tech": "SCIENCE_TWO",
        "placer": "rabbithouse_placer",
        "notes": "",
    },
    {
        "name": "birdcage",
        "ingredients": {"papyrus": 2, "goldnugget": 6, "seeds": 2},
        "tab": "TOWN",
        "tech": "SCIENCE_TWO",
        "placer": "birdcage_placer",
        "notes": "",
    },
    # ...existing code...
    # TOOLS
    {
        "name": "axe",
        "ingredients": {"twigs": 1, "flint": 1},
        "tab": "TOOLS",
        "tech": "NONE",
        "placer": None,
        "notes": "",
    },
    {
        "name": "pickaxe",
        "ingredients": {"twigs": 2, "flint": 2},
        "tab": "TOOLS",
        "tech": "NONE",
        "placer": None,
        "notes": "",
    },
    {
        "name": "shovel",
        "ingredients": {"twigs": 2, "flint": 2},
        "tab": "TOOLS",
        "tech": "SCIENCE_ONE",
        "placer": None,
        "notes": "",
    },
    {
        "name": "hammer",
        "ingredients": {"twigs": 3, "rocks": 3, "rope": 2},
        "tab": "TOOLS",
        "tech": "SCIENCE_ONE",
        "placer": None,
        "notes": "",
    },
    # ...existing code...
]

# Index for fast lookup by name
RECIPES_BY_NAME = {r["name"]: r for r in RECIPES}
