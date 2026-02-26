# TheWorld & World State

## Accessing the World

```lua
local world = GetWorld()                  -- global helper, works anywhere
local world = GLOBAL.GetWorld()           -- from modmain.lua
```

`GetWorld()` returns the world entity. All world subsystems live under
`world.components.<name>`.

---

## Clock — Time of Day & Day Number

```lua
local clock = GetClock()   -- global shorthand
-- or
local clock = GetWorld().components.clock
```

| Method | Returns | Notes |
|---|---|---|
| `clock:GetDay()` | `int` | Current day number (1-based) |
| `clock:GetDayTime()` | `float 0-1` | 0=start of day, 1=end |
| `clock:GetNormTime()` | `float 0-1` | Normalised across full day cycle |
| `clock:GetPhase()` | `"day"\|"dusk"\|"night"` | Named phase ✅ use this for prompts |
| `clock:IsDay()` | `bool` | |
| `clock:IsDusk()` | `bool` | |
| `clock:IsNight()` | `bool` | |
| `clock:GetMoonPhase()` | `string` | |
| `clock:GetTimeLeftInEra()` | `float` | Seconds left in current phase |

---

## SeasonManager — Season & Weather

```lua
local sm = GetWorld().components.seasonmanager
-- or
local sm = GetSeasonManager()   -- global helper
```

| Method / Field | Returns | Notes |
|---|---|---|
| `sm:GetSeason()` | `"autumn"\|"winter"\|"summer"\|"spring"` | ✅ correct season API |
| `sm:IsRaining()` | `bool` | True when precipitation is active |
| `sm:GetSeasonLength()` | `int` | Days in current season |
| `sm:GetDaysLeftInSeason()` | `int` | |
| `sm:GetPrecipitationRate()` | `float` | 0 = dry, higher = heavier rain |
| `sm.atmo_moisture` | `float` | Internal moisture accumulator |
| `sm.current_temperature` | `float` | World temperature (not player temp) |

### ⚠ Common mistake — broken season API

```lua
-- WRONG: clock:GetSeason() + GLOBAL.SEASONS does NOT work in DS single-player
local season_idx = clock:GetSeason()          -- always nil
local season = GLOBAL.SEASONS[season_idx]     -- crashes / returns nil

-- CORRECT:
local season = GetWorld().components.seasonmanager:GetSeason()
-- returns "autumn", "winter", "summer", or "spring" directly
```

---

## Nearby Entity Search

```lua
-- Find all entities within radius around a point
local pos = Vector3(player.Transform:GetWorldPosition())
local ents = TheSim:FindEntities(pos.x, pos.y, pos.z, radius)

-- Filter by tags (only entities that have ALL listed tags)
local hostiles = TheSim:FindEntities(pos.x, pos.y, pos.z, 20, {"hostile"})

-- Useful entity checks
ent:HasTag("hostile")               -- combat-active enemy
ent:HasTag("edible")                -- can be eaten
ent:HasTag("campfire")              -- campfire entity
ent.components.workable             -- can be chopped/mined
ent.components.container            -- chest/backpack
```

---

## Map

```lua
local map = GetWorld().Map
local tile = map:GetTileAtPoint(x, 0, z)
local is_passable = map:IsPassableAtPoint(x, 0, z)
```