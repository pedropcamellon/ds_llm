# Prefabs Reference

> **Stub** — fill in as you research or encounter relevant API calls.

## What is a Prefab?

A "prefab" (prefabricated entity) is a factory function that creates and
configures an entity. It defines what components, tags, assets, and visuals
an entity has. Examples: `wilson`, `campfire`, `axe`.

## Declaring in modmain.lua

```lua
PrefabFiles = { "my_prefab" }           -- loads scripts/prefabs/my_prefab.lua
```

## Prefab Skeleton

```lua
-- scripts/prefabs/my_prefab.lua
local assets = {
    Asset("ANIM", "anim/my_anim.zip"),
}

local function fn(Sim)
    local inst = CreateEntity()
    inst.entity:AddTransform()
    inst.entity:AddAnimState()
    inst.entity:AddPhysics()

    inst.AnimState:SetBank("my_bank")
    inst.AnimState:SetBuild("my_build")
    inst.AnimState:PlayAnimation("idle", true)

    inst:AddTag("mytag")
    inst:AddComponent("inspectable")

    return inst
end

return Prefab("common/my_prefab", fn, assets)
```

## Spawning a Prefab

```lua
local ent = GLOBAL.SpawnPrefab("my_prefab")
ent.Transform:SetPosition(x, y, z)
```

## Post-Init Hook

```lua
-- Runs after any "wilson" prefab is created (modmain.lua)
AddPrefabPostInit("wilson", function(inst)
    inst:AddComponent("my_component")
end)
```

## TODO
- [ ] Tags reference (common built-in tags)
- [ ] AnimState API
- [ ] Physics shapes
- [ ] MiniMapEntity setup
