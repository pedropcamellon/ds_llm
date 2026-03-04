"""
entity_sets.py — Static sets and maps that classify Don't Starve prefabs
and entity names into behavioural categories.

Single responsibility: be the single source of truth for what is edible,
harvestable, pickable, or hostile. No logic lives here.
"""

# Items the player can eat directly from inventory (no cooking required)
EDIBLE_PREFABS: frozenset[str] = frozenset(
    {
        "berries",
        "berries_cooked",
        "carrot",
        "carrot_cooked",
        "mushroom",
        "mushroom_cooked",
        "red_mushroom",
        "red_cap",
        "green_mushroom",
        "green_cap",
        "blue_mushroom",
        "blue_cap",
        "monstermeat",
        "monstermeat_dried",
        "meat",
        "meat_dried",
        "morsel",
        "morsel_dried",
        "smallmeat",
        "tinymeat",
        "jerky",
        "smalljerky",
        "egg",
        "cookedegg",
        "fish",
        "cookedfish",
        "froggylegs",
        "cookedfroggylegs",
        "honey",
        "honeyham",
        "taffy",
        "butterflywings",
        "cookedbutterflywings",
        "hotchili",
        "meatballs",
        "trailmix",
        "kabobs",
        "potatosouffle",
        "dragonpie",
        "waffles",
        "mandrakesoup",
        "stuffedeggplant",
        "fruitmedley",
        "fistfulofgame",
        "seeds",
        "pinecone",
    }
)

# Harvestable entity names → what resource they yield when harvested
HARVESTABLE_ENTITIES: dict[str, str] = {
    "twig_plant": "twigs",
    "sapling": "twigs",
    "grass": "cutgrass",
    "cutgrass": "cutgrass",
    "grasstuft": "cutgrass",
    "flint": "flint",
    "rocks": "rocks",
    # Boulder nodes (all need pickaxe — see HARVEST_REQUIRES_TOOL):
    #   rock1/rock2 → rocks (+ flint drop handled by DS internally)
    #   rock_flintless → rocks only (depleted/cave variant, no flint drop)
    #   rock_flint → flint (surface flint-specific node)
    #   rock_ore → goldnugget
    "rock_flint": "flint",
    "rock_ore": "goldnugget",
    "rock_flintless": "rocks",
    "goldnugget": "goldnugget",
    "berrybush": "berries",
    "berrybush2": "berries",
    "carrot_planted": "carrot",
    "mushroom_tree": "mushroom",
    "pinecone": "pinecone",
    "reeds": "papyrus",
    "marsh_plant": "cutgrass",
    "fireflies": "fireflies",
    "pond": "fish",
    # Trees (chop with axe; also shows as gather option when axe in inventory)
    "evergreen": "log",
    "birchnutt_tree": "log",
    "lumpy_evergreen": "log",
    "deciduoustree": "log",
    # Boulder entities (mine with pickaxe).
    # rock1 / rock2 are the standard overworld variants — yield rocks + flint.
    # rock_flintless is a depleted/cave variant — same pickaxe requirement but
    # yields only rocks (no flint drop), hence the name.
    "rock1": "rocks",
    "rock2": "rocks",
    # Other
    "rabbithole": "manrabbit_tail",  # can trap rabbits here
    "beehive": "honey",
    "spiderden": "silk",
    "cave_entrance": "explore",
}

# Entities that can only be harvested when a specific tool is present.
# Any entity listed here will be skipped by ConcreteActionBuilder if the
# required item is absent from the player's inventory.
# Key: entity name (lowercase)  →  Value: required inventory prefab
HARVEST_REQUIRES_TOOL: dict[str, str] = {
    # Trees need an axe (otherwise it's just "chop_tree" which is blocked)
    "evergreen": "axe",
    "birchnutt_tree": "axe",
    "lumpy_evergreen": "axe",
    "deciduoustree": "axe",
    # Boulders need a pickaxe. Three variants:
    #   rock1 / rock2    — standard overworld boulders, drop rocks + flint
    #   rock_flintless   — depleted/cave variant, drops rocks only (no flint)
    #   rock_flint       — flint-specific surface node, drops flint
    #   rock_ore         — gold ore node, drops goldnugget
    "rock1": "pickaxe",
    "rock2": "pickaxe",
    "rock_flintless": "pickaxe",
    "rocks": "pickaxe",
    "rock_flint": "pickaxe",
    "rock_ore": "pickaxe",
}

# Prefabs that are loose ground items worth picking up
PICKUP_PREFABS: frozenset[str] = frozenset(
    {
        "log",
        "boards",
        "twigs",
        "cutgrass",
        "flint",
        "rocks",
        "goldnugget",
        "nitre",
        "charcoal",
        "ash",
        "berries",
        "carrot",
        "mushroom",
        "seeds",
        "silk",
        "spidergland",
        "hound_tooth",
        "manrabbit_tail",
        "pigskin",
        "petals",
        "pinecone",
        "red_gem",
        "blue_gem",
        "rope",
        "papyrus",
        "blueprints",
        "meat",
        "morsel",
        "egg",
        "honey",
        "fireflies",
        "lightbulb",
    }
)

# Entity *type* values that mark an entity as hostile
HOSTILE_TYPES: frozenset[str] = frozenset(
    {
        "hostile",
        "monster",
        "mob",
        "enemy",
    }
)

# Entity *name* values that are always hostile (supplements type check)
HOSTILE_ENTITIES: frozenset[str] = frozenset(
    {
        "spider",
        "spider_warrior",
        "hound",
        "treeguard",
        "tentacle",
        "shadowcreature",
        "ghost",
        "deerclops",
        "bearger",
        "dragonfly",
        "beequeen",
        "leif",
        "leif_sparse",
        "minotaur",
        "Klaus",
        "nightmare_throne",
        "slurper",
        "slurtle",
        "snurtle",
    }
)
