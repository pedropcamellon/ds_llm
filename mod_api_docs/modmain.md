# modmain.lua Reference

> **Stub** — fill in as you research or encounter relevant API calls.

## Purpose

`modmain.lua` is the main hook script loaded by the game engine. It wires your
mod into the game using the global mod API functions exposed by the engine.

## Key Global Hook Functions

| Function                               | When it fires                                           |
| -------------------------------------- | ------------------------------------------------------- |
| `AddPrefabPostInit(prefab, fn)`        | After a named prefab entity is created                  |
| `AddPlayerPostInit(fn)`                | After the local player entity is created                |
| `AddComponentPostInit(name, fn)`       | After a component is instantiated on any entity         |
| `AddBrainPostInit(name, fn)`           | After a brain is instantiated                           |
| `AddSimPostInit(fn)`                   | After the simulation has initialised (HUD is available) |
| `AddClassPostConstruct(classpath, fn)` | After a class constructor runs                          |

## Loading Other Scripts

```lua
-- In modmain.lua — must use GLOBAL.require
local MyComponent = GLOBAL.require "components/my_component"

-- In component/brain files — plain require works
local utils = require "components/json_utils"
```

## Useful Globals

```lua
GLOBAL.GetPlayer()          -- local player entity
GLOBAL.GetWorld()           -- world entity
GLOBAL.SpawnPrefab(name)    -- spawn an entity by prefab name
GLOBAL.TheInput             -- input handler
GLOBAL.IsPaused()           -- bool
GLOBAL.c_give(item, count)  -- debug: give item to player
```

## Loading Scripts

Two ways to load Lua scripts from your mod:

### `require`
https://www.lua.org/pil/8.1.html

Loads a script once — subsequent calls return the cached result.
Path is relative to the DS `scripts/` directory (or mod scripts folder via `GLOBAL.require`).

```lua
-- modmain.lua (must prefix with GLOBAL)
local MyComponent = GLOBAL.require "components/my_component"

-- Inside component / brain files (plain require works)
local utils = require "components/json_utils"
```

### `modimport`
Loads a file relative to **your mod directory**. The `.lua` extension is optional.
Calls `kleiloadlua` internally and sets the result to the mod environment.

```lua
modimport("scripts/myhelper")        -- loads mods/<yourmod>/scripts/myhelper.lua
modimport("scripts/myhelper.lua")    -- same thing
```

> Use `modimport` when you want to load a file relative to your mod folder
> without worrying about the global script path.

---

## PrefabFiles

Tells the engine which prefab scripts to load from your mod's `scripts/prefabs/` folder.

```lua
PrefabFiles = {
    "my_prefab",       -- loads scripts/prefabs/my_prefab.lua
    "range",           -- loads scripts/prefabs/range.lua
}
```

---

## Assets

Declares all asset files your mod needs so the engine can load them before the
game starts. See [Assets reference](assets.md) *(stub)* for all asset types.

```lua
Assets = {
    Asset("IMAGE", "images/my_texture.tex"),
    Asset("ATLAS", "images/my_texture.xml"),
    Asset("ANIM",  "anim/my_anim.zip"),
    Asset("SOUND", "sound/my_bank.fsb"),
}
```

Common asset types:

| Type | File |
|------|------|
| `"IMAGE"` | `.tex` texture |
| `"ATLAS"` | `.xml` atlas descriptor |
| `"ANIM"` | `.zip` animation bundle |
| `"SOUND"` | `.fsb` FMOD sound bank |

---

## TODO — sections to expand
- [ ] `AddRecipe` / `AddIngredient`
- [ ] Event system (`ListenForEvent`, `PushEvent`)
- [ ] Task scheduling (`DoTaskInTime`, `DoPeriodicTask`)
- [ ] Assets reference page (`assets.md`)
