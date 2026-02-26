# The Player Entity

> **Stub** — fill in as you research or encounter relevant API calls.

## Getting the Player

```lua
local player = GLOBAL.GetPlayer()   -- from modmain.lua
local player = self.inst            -- from inside a component/brain
```

## Vital Stats

```lua
-- Health
player.components.health.currenthealth   -- number
player.components.health.maxhealth
player.components.health:IsDead()        -- bool

-- Hunger
player.components.hunger.current
player.components.hunger.max

-- Sanity
player.components.sanity.current
player.components.sanity.max
```

## Position & Movement

```lua
local x, y, z = player.Transform:GetWorldPosition()
player.Transform:SetPosition(x, y, z)
player:FacePoint(x, y, z)

-- Locomotion
player.components.locomotor:WalkForward()
player.components.locomotor:Stop()
player.components.locomotor:GoToPoint(Point(x, y, z))
player.components.locomotor:GoToEntity(target)
```

## Tags

```lua
player:AddTag("ArtificalWilson")
player:RemoveTag("ArtificalWilson")
player:HasTag("player")             -- true for player entity
```

## Events

```lua
player:ListenForEvent("attacked",   function(inst, data) end)
player:ListenForEvent("death",      function(inst, data) end)
player:ListenForEvent("hungerdelta",function(inst, data) end)

player:PushEvent("my_event", { key = value })
```

## Tasks & Timers

```lua
player:DoTaskInTime(3.0, function(inst) end)       -- fire once after delay
player:DoPeriodicTask(5.0, function(inst) end)     -- repeat every N seconds
```

## TODO
- [ ] Equipment slots (head, body, hand)
- [ ] Crafting / `builder` component
- [ ] Brain / AI control (`SetBrain`)
- [ ] HUD access (`player.HUD`)
