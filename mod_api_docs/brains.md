# Brains & Behaviour Trees

> **Stub** — fill in as you research or encounter relevant API calls.

## Overview

A "brain" is a Lua script that defines an AI behaviour tree for an entity.
The engine evaluates the tree each tick and picks the highest-priority
action whose conditions are met.

## Setting a Brain

```lua
-- Give an entity a brain (modmain.lua or component)
local brain = GLOBAL.require "brains/artificalwilson"
player:SetBrain(brain)

-- Revert to default
local wilsonbrain = GLOBAL.require "brains/wilsonbrain"
player:SetBrain(wilsonbrain)
```

## Brain Skeleton

```lua
-- scripts/brains/my_brain.lua
require "behaviours/wander"
require "behaviours/chaseandattack"

local MyBrain = Class(Brain, function(self, inst)
    Brain._ctor(self, inst)
end)

function MyBrain:OnStart()
    local root = PriorityNode({
        -- highest priority first
        WhileNode(function() return self.inst.components.health:IsDead() end, "Dead",
            ActionNode(function() end)),

        ChaseAndAttack(self.inst, MAX_CHASE_DIST),
        Wander(self.inst),
    }, 0.5)

    self.bt = BT(self.inst, root)
end

return MyBrain
```

## Common Behaviour Nodes

| Node                             | Purpose                                 |
| -------------------------------- | --------------------------------------- |
| `PriorityNode(children, period)` | Pick first child whose condition passes |
| `SequenceNode(children)`         | Run children in order; stop on failure  |
| `WhileNode(cond, name, child)`   | Run child while condition is true       |
| `ActionNode(fn)`                 | Execute a single action function        |
| `ConditionNode(fn)`              | True/false gate                         |
| `WaitNode(duration)`             | Pause for N seconds                     |

## Custom Behaviours in this Mod

| File                              | Behaviour               |
| --------------------------------- | ----------------------- |
| `behaviours/managehunger.lua`     | Eat food when hungry    |
| `behaviours/selfpreservation.lua` | Run from threats        |
| `behaviours/findtreeorrock.lua`   | Chop / mine resources   |
| `behaviours/cookfood.lua`         | Cook raw food at a fire |
| `behaviours/gordonramsay.lua`     | Advanced cooking logic  |
| `behaviours/manageinventory.lua`  | Drop excess items       |

## TODO
- [ ] `BT` tick rate / period tuning
- [ ] Sleep / DoTaskInTime inside behaviours
- [ ] Passing state between behaviour nodes
- [ ] LLM action dispatcher node
