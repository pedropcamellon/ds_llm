# Components Reference

> **Stub** — fill in as you research or encounter relevant API calls.

## What is a Component?

Components are Lua tables attached to entities that add data and behaviour.
They live in `scripts/components/` (game) or `mods/<mod>/scripts/components/` (mod).

## Attaching a Component

```lua
entity:AddComponent("my_component")
entity:RemoveComponent("my_component")
local comp = entity.components.my_component
```

## Component Skeleton

```lua
-- scripts/components/my_component.lua
local MyComponent = Class(function(self, inst)
    self.inst = inst
    -- initialise fields
end)

function MyComponent:OnSave()
    return { somedata = self.somedata }
end

function MyComponent:OnLoad(data)
    if data then
        self.somedata = data.somedata
    end
end

function MyComponent:GetDebugString()
    return tostring(self.somedata)
end

return MyComponent
```

## Registering in modmain.lua

Components are auto-discovered from `scripts/components/` — no explicit
registration needed. Just add the file and call `entity:AddComponent("name")`.

## TODO — common components to document
- [ ] `health`
- [ ] `hunger`
- [ ] `sanity`
- [ ] `inventory`
- [ ] `combat`
- [ ] `locomotor`
- [ ] `follower` / `homeseeker`
- [ ] `prioritizer` (custom)
- [ ] `llm_state_exporter` (custom)
- [ ] `llm_action_executor` (custom)
