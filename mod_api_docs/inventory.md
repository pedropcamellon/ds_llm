# Inventory Component

> **Stub** — fill in as you research or encounter relevant API calls.

## Accessing the Inventory

```lua
local inv = player.components.inventory
```

## Reading Items

```lua
-- Don't Starve SINGLE-PLAYER — use itemslots table
for slot, item in pairs(inv.itemslots) do
    print(slot, item.prefab)
end

-- Get item in a specific slot (1-based)
local item = inv:GetItemInSlot(1)
if item then
    print(item.prefab, item.components.stackable and item.components.stackable.stacksize or 1)
end

-- Find first item matching a prefab name
local axe = inv:FindItem(function(item) return item.prefab == "axe" end)

-- Equipped items
local handheld = inv:GetEquippedItem(EQUIPSLOTS.HANDS)
local head     = inv:GetEquippedItem(EQUIPSLOTS.HEAD)
local body     = inv:GetEquippedItem(EQUIPSLOTS.BODY)
```

## Stack Counts

```lua
-- Item count (stackable items)
local count = item.components.stackable and item.components.stackable.stacksize or 1
```

## Useful Checks

```lua
inv:IsFull()           -- bool, standard slots full
inv:IsEmpty()          -- bool
inv:NumItems()         -- count of occupied slots

-- Custom extension added in modmain.lua:
inv:IsTotallyFull()    -- standard slots AND overflow container both full
```

## Giving / Dropping Items

```lua
inv:GiveItem(item)
inv:DropItem(item)
```

## Common Prefab Names (for reference)

| Prefab | Description |
|--------|-------------|
| `log` | Wood log |
| `twigs` | Twigs |
| `cutgrass` | Grass |
| `flint` | Flint |
| `rocks` | Rocks |
| `goldnugget` | Gold nugget |
| `axe` | Axe |
| `pickaxe` | Pickaxe |
| `campfire` | Campfire (placed) |
| `torch` | Torch |

## TODO
- [ ] `FindItems` (DST) vs `itemslots` (DS) differences
- [ ] Equipment equip/unequip API
- [ ] Overflow / backpack container
- [ ] Crafting from inventory
