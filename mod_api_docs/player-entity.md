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
player:ListenForEvent("builditem",  function(inst, data) end)  -- data.item, data.recipe
player:ListenForEvent("buildstructure", function(inst, data) end)

player:PushEvent("my_event", { key = value })
```

## Speech / Talker Component

Wilson speaks via the `talker` component. Hook `ontalk` to capture every speech bubble.

### ⚠ Critical: errors in `ontalk` kill the speech bubble

`Say()` calls `self.ontalk(inst, script)` synchronously, then immediately calls
`inst:StartThread(sayfn)` to render the bubble. If your hook throws an unhandled
error, `Say()` aborts before the thread starts — **no bubble appears in-game**,
but the hook ran far enough to log the text. Always wrap hook bodies in `pcall`:

```lua
-- fires before each Say() call — script is string or {message, duration, noanim}[]
local orig = player.components.talker.ontalk
player.components.talker.ontalk = function(talker_inst, script)
    -- MUST pcall — any error here cancels the speech bubble rendering
    pcall(function()
        local text = type(script) == "string" and script
                   or (type(script) == "table" and script[1] and script[1].message)
                   or ""
        if text ~= "" then
            -- do something with text, e.g. table.insert into a buffer
        end
    end)
    if orig then orig(talker_inst, script) end
end
```

Note: use a distinct parameter name (e.g. `talker_inst`) to avoid shadowing the
outer `inst` / `self.inst` closures.

### How `Say()` works internally (talker.lua lines 80–120)

```
Say(script, time, noanim)
  → dead/asleep/ignoring guards
  → if self.ontalk then self.ontalk(self.inst, script) end   ← our hook
  → ShutUp()  (cancel old bubble)
  → self.task = inst:StartThread(sayfn)  ← renders the bubble widget
```

`sayfn` coroutine fires `ontalk` event per line and calls `Sleep(line.duration)`.
`ontalk` callback fires **once per `Say()` call**, not once per line.

### Speech strings

Come from `data/scripts/speech_wilson.lua`. Key failure strings:

- `"I don't have the right tools."` — wrong/missing tool for action
- `"I can't learn that one."` — recipe locked
- `"I can't pay for that."` — missing ingredients for crafting
- `"Take that, nature!"` — tree chopped successfully
- `"It's my trusty axe."` — examining axe
- `"I don't think an axe will cut it."` — trying to chop marble tree

Trigger speech manually:

```lua
player.components.talker:Say("Hello world", 3.0)  -- text, duration_seconds
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
