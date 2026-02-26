--[[
    TODO LLM Action Executor Component
    
    Reads action commands from an external JSON file and executes them.
    This allows an external LLM agent to issue commands to the game.
    
    Reads from: mods/DS-AI-master/state/action_command.json
    Format: {"action": "action_name", "reason": "why we're doing this"}
    
    Supported actions:
    - move_to_food: Find and move to nearby food
    - chop_tree: Find and chop a tree
    - mine_rock: Find and mine a rock
    - pick_up_item: Find and pick up nearby items
    - craft_item:<item_name>: Craft a specific item
    - eat_food: Eat food from inventory
    - cook_food: Cook food at a nearby fire/cooking pot
    - run_from_enemy: Run away from hostile entities
    - attack_enemy: Attack nearest hostile
    - explore: Move to an unexplored area
    - idle: Do nothing
]] --
local LLMActionExecutor = Class(function(self, inst)
    self.inst = inst
    self.action_file = "mods/DS-AI-master/state/action_command.json"
    self.last_action_file_mtime = 0
    self.poll_interval = 1.0 -- Check for new actions every 1 second
    self.last_poll_time = 0

    -- Reference to the brain (will be set when brain starts)
    self.brain = nil

    -- Current action being executed
    self.current_action = nil
    self.current_action_timeout = 0
    self.action_timeout_duration = 30 -- Force abort action after 30 seconds
end)

function LLMActionExecutor:SetBrain(brain)
    self.brain = brain
end

function LLMActionExecutor:ParseJSON(json_str)
    -- Very simple JSON parsing for our specific format
    -- This is a basic implementation; a full JSON library would be better
    -- But we need to avoid external dependencies

    local result = {}

    -- Look for "action": "..."
    local action_match = json_str:match('"action"%s*:%s*"([^"]*)"')
    if action_match then
        result.action = action_match
    end

    -- Look for "reason": "..."
    local reason_match = json_str:match('"reason"%s*:%s*"([^"]*)"')
    if reason_match then
        result.reason = reason_match
    end

    return result
end

function LLMActionExecutor:FileModified()
    -- Check if the action file has been modified (very basic check)
    -- In a real system, we'd use inotify or similar
    -- For now, we just check if the file exists

    local f = io.open(self.action_file, "r")
    if not f then
        return false
    end
    f:close()
    return true
end

function LLMActionExecutor:ReadActionCommand()
    local f = io.open(self.action_file, "r")
    if not f then
        return nil
    end

    local json_str = f:read("*a")
    f:close()

    if not json_str or json_str == "" then
        return nil
    end

    local action_cmd = self:ParseJSON(json_str)
    return action_cmd
end

function LLMActionExecutor:ExecuteAction(action_name, reason)
    if not self.inst or not self.inst:IsValid() then
        return
    end

    print("[LLMActionExecutor] Executing action: " .. action_name .. " - " .. reason)

    -- Store current action
    self.current_action = action_name
    self.current_action_timeout = 0

    -- Route to appropriate handler
    if action_name == "move_to_food" then
        self:ActionMoveToFood()
    elseif action_name == "chop_tree" then
        self:ActionChopTree()
    elseif action_name == "mine_rock" then
        self:ActionMineRock()
    elseif action_name == "pick_up_item" then
        self:ActionPickUpItem()
    elseif action_name:match("^craft_item:") then
        local item_name = action_name:match("^craft_item:(.+)$")
        self:ActionCraftItem(item_name)
    elseif action_name == "eat_food" then
        self:ActionEatFood()
    elseif action_name == "cook_food" then
        self:ActionCookFood()
    elseif action_name == "run_from_enemy" then
        self:ActionRunFromEnemy()
    elseif action_name == "attack_enemy" then
        self:ActionAttackEnemy()
    elseif action_name == "explore" then
        self:ActionExplore()
    elseif action_name == "idle" then
        self:ActionIdle()
    else
        print("[LLMActionExecutor] Unknown action: " .. action_name)
    end
end

function LLMActionExecutor:ActionMoveToFood()
    -- Find a food item within reasonable distance
    local player_pos = Vector3(self.inst.Transform:GetWorldPosition())
    local food = FindEntity(self.inst, 30, function(item)
        return item:HasTag("edible") and not self.inst.components.prioritizer:OnIgnoreList(item.prefab)
    end)

    if food then
        local action = BufferedAction(self.inst, food, ACTIONS.PICKUP)
        self.inst:PushBufferedAction(action)
    else
        print("[LLMActionExecutor] No food found nearby")
    end
end

function LLMActionExecutor:ActionChopTree()
    -- Find a tree and chop it
    local tree = FindEntity(self.inst, 30, function(item)
        return item:HasTag("tree") and not self.inst.components.prioritizer:OnIgnoreList(item.prefab)
    end)

    if tree then
        local action = BufferedAction(self.inst, tree, ACTIONS.CHOP)
        self.inst:PushBufferedAction(action)
    else
        print("[LLMActionExecutor] No tree found nearby")
    end
end

function LLMActionExecutor:ActionMineRock()
    -- Find a rock and mine it
    local rock = FindEntity(self.inst, 30, function(item)
        return item:HasTag("rock") and not self.inst.components.prioritizer:OnIgnoreList(item.prefab)
    end)

    if rock then
        local action = BufferedAction(self.inst, rock, ACTIONS.MINE)
        self.inst:PushBufferedAction(action)
    else
        print("[LLMActionExecutor] No rock found nearby")
    end
end

function LLMActionExecutor:ActionPickUpItem()
    -- Find any pickupable item
    local item = FindEntity(self.inst, 20, function(entity)
        return entity.components.inventoryitem and entity:IsValid() and
                   not self.inst.components.prioritizer:OnIgnoreList(entity.prefab)
    end)

    if item then
        local action = BufferedAction(self.inst, item, ACTIONS.PICKUP)
        self.inst:PushBufferedAction(action)
    else
        print("[LLMActionExecutor] No items to pick up")
    end
end

function LLMActionExecutor:ActionCraftItem(item_name)
    -- Try to craft a specific item
    if not self.inst.components.builder then
        print("[LLMActionExecutor] No builder component")
        return
    end

    local recipe = GetRecipe(item_name)
    if not recipe then
        print("[LLMActionExecutor] Recipe not found: " .. item_name)
        return
    end

    -- Check if we know the recipe
    if not self.inst.components.builder:KnowsRecipe(item_name) then
        print("[LLMActionExecutor] Recipe unknown: " .. item_name)
        return
    end

    -- Try to build it
    if self.inst.components.builder:CanBuild(item_name) then
        -- Find a valid build position nearby
        local pos = self.inst.brain:GetPointNearThing(self.inst, 3)
        if pos then
            local action = BufferedAction(self.inst, self.inst, ACTIONS.BUILD, nil, pos, item_name, nil)
            self.inst:PushBufferedAction(action)
        end
    else
        print("[LLMActionExecutor] Missing ingredients for: " .. item_name)
    end
end

function LLMActionExecutor:ActionEatFood()
    -- Find edible food in inventory and eat it
    local food = self.inst.components.inventory:FindItem(function(item)
        return item:HasTag("edible")
    end)

    if food then
        local action = BufferedAction(self.inst, food, ACTIONS.EAT)
        self.inst:PushBufferedAction(action)
    else
        print("[LLMActionExecutor] No food in inventory to eat")
    end
end

function LLMActionExecutor:ActionCookFood()
    -- Find a cooking device (cookpot or campfire) and cook
    local cooking_device = FindEntity(self.inst, 15, function(item)
        return item:HasTag("campfire") or item.prefab == "cookpot"
    end)

    if cooking_device then
        -- This is a complex action - would need to implement full cooking logic
        -- For now, just move towards it
        local action = BufferedAction(self.inst, cooking_device, ACTIONS.LOOKAT)
        self.inst:PushBufferedAction(action)
        print("[LLMActionExecutor] Moved to cooking device; cooking not fully implemented")
    else
        print("[LLMActionExecutor] No cooking device found")
    end
end

function LLMActionExecutor:ActionRunFromEnemy()
    -- Find nearest threat and run away
    local hostile = FindEntity(self.inst, 20, function(entity)
        return entity:HasTag("hostile") and self.inst.components.combat:CanTarget(entity)
    end)

    if hostile then
        local away_pos = self.inst.brain:GetPointNearThing(self.inst, 10)
        if away_pos then
            self.inst.components.locomotor:GoToPoint(away_pos)
        end
    else
        print("[LLMActionExecutor] No hostile enemies nearby")
    end
end

function LLMActionExecutor:ActionAttackEnemy()
    -- Find and attack nearest hostile
    local hostile = FindEntity(self.inst, 20, function(entity)
        return entity:HasTag("hostile") and self.inst.components.combat:CanTarget(entity)
    end)

    if hostile then
        self.inst.components.combat:SetTarget(hostile)
    else
        print("[LLMActionExecutor] No hostile enemies to attack")
    end
end

function LLMActionExecutor:ActionExplore()
    -- Move to a nearby unexplored location
    if self.brain then
        self.brain:IncreaseSearchDistance()
    end

    local random_pos = self.inst.brain:GetPointNearThing(self.inst, 20)
    if random_pos then
        self.inst.components.locomotor:GoToPoint(random_pos)
    end
end

function LLMActionExecutor:ActionIdle()
    -- Do nothing
    print("[LLMActionExecutor] Idle action")
end

function LLMActionExecutor:OnUpdate(dt)
    -- Check for new action commands periodically
    self.last_poll_time = self.last_poll_time + dt

    if self.last_poll_time >= self.poll_interval then
        local action_cmd = self:ReadActionCommand()

        if action_cmd and action_cmd.action then
            self:ExecuteAction(action_cmd.action, action_cmd.reason or "")
        end

        self.last_poll_time = 0
    end

    -- Update action timeout
    if self.current_action then
        self.current_action_timeout = self.current_action_timeout + dt
        if self.current_action_timeout > self.action_timeout_duration then
            print("[LLMActionExecutor] Action timeout: " .. self.current_action)
            self.current_action = nil
        end
    end
end

return LLMActionExecutor
