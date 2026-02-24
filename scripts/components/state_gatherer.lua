--[[
    State Gatherer
    
    Collects all game state data (player vitals, inventory, nearby entities, etc)
]] --
local StateGatherer = {}

function StateGatherer.GetPlayerVitals(player)
    local health = 0
    local hunger = 0
    local sanity = 0

    local success = pcall(function()
        if player.components.health then
            health = math.ceil(player.components.health.currenthealth) or 0
        end
        if player.components.hunger then
            hunger = math.ceil(player.components.hunger.current) or 0
        end
        if player.components.sanity then
            sanity = math.ceil(player.components.sanity.current) or 0
        end
    end)

    return health, hunger, sanity
end

function StateGatherer.GetTimeInfo(clock)
    if not clock then
        return 0, 0, "unknown"
    end

    local day = 0
    local time_of_day = 0
    local season = "unknown"

    local success = pcall(function()
        day = clock:GetDay() or 0
        time_of_day = clock:GetDayTime() or 0

        if GLOBAL.SEASONS then
            local season_idx = clock:GetSeason()
            if season_idx and GLOBAL.SEASONS[season_idx] then
                season = GLOBAL.SEASONS[season_idx]
            end
        end
    end)

    return day, time_of_day, season
end

function StateGatherer.GetInventory(player)
    local inventory = {}
    local equipped = "none"

    local success, err = pcall(function()
        if not player.components.inventory then
            print("[ERROR] [StateGatherer] No inventory component")
            return
        end

        local items = {}
        -- Use itemslots (Don't Starve single-player)
        if player.components.inventory.itemslots then
            for i, item in ipairs(player.components.inventory.itemslots) do
                if item then
                    table.insert(items, item)
                end
            end
        end
        -- Fallback: FindItem (first found only)
        if (#items == 0) and player.components.inventory.FindItem then
            local found = player.components.inventory:FindItem(function(item)
                return item and item.prefab
            end)
            if found then
                items = {found}
            end
        end
        if #items == 0 then
            print("[ERROR] [StateGatherer] Could not retrieve inventory items (itemslots/FindItem)")
            return
        end
        local item_counts = {}
        for _, item in ipairs(items) do
            if item and item.prefab then
                local prefab = item.prefab
                if item_counts[prefab] then
                    item_counts[prefab] = item_counts[prefab] + 1
                else
                    item_counts[prefab] = 1
                end
            end
        end
        for prefab, count in pairs(item_counts) do
            if count > 1 then
                table.insert(inventory, prefab .. " x" .. count)
            else
                table.insert(inventory, prefab)
            end
        end
        local equipped_item = player.components.inventory:GetEquippedItem(EQUIPSLOTS.HANDS)
        if equipped_item and equipped_item.prefab then
            equipped = equipped_item.prefab
        end
    end)
    if not success then
        print("[ERROR] [StateGatherer] GetInventory pcall error: " .. tostring(err))
    end
    return inventory, equipped
end

function StateGatherer.GetPosition(player)
    local x = 0
    local z = 0

    local success = pcall(function()
        local pos = Vector3(player.Transform:GetWorldPosition())
        x = math.ceil(pos.x * 10) / 10 or 0
        z = math.ceil(pos.z * 10) / 10 or 0
    end)

    return {
        x = x,
        z = z
    }
end

function StateGatherer.GetNearbyEntities(player, radius)
    radius = radius or 30
    local entities = {}

    local success = pcall(function()
        local player_pos = Vector3(player.Transform:GetWorldPosition())
        if not player_pos then
            return
        end

        local all_entities = TheSim:FindEntities(player_pos.x, player_pos.y, player_pos.z, radius)
        if not all_entities then
            return
        end

        for _, entity in ipairs(all_entities) do
            if entity and entity ~= player and entity:IsValid() then
                local entity_pos = Vector3(entity.Transform:GetWorldPosition())
                if entity_pos then
                    local distance = math.sqrt((entity_pos.x - player_pos.x) ^ 2 + (entity_pos.z - player_pos.z) ^ 2)

                    local entity_name = entity.prefab or "unknown"
                    local entity_type = "unknown"

                    if entity:HasTag("hostile") then
                        entity_type = "hostile"
                    elseif entity:HasTag("edible") then
                        entity_type = "food"
                    elseif entity.components and entity.components.workable then
                        entity_type = "harvestable"
                    elseif entity.components and entity.components.container then
                        entity_type = "container"
                    elseif entity:HasTag("campfire") or entity:HasTag("fire") then
                        entity_type = "fire"
                    else
                        entity_type = "other"
                    end

                    table.insert(entities, {
                        name = entity_name,
                        type = entity_type,
                        distance = math.ceil(distance * 10) / 10
                    })
                end
            end
        end

        table.sort(entities, function(a, b)
            return a.distance < b.distance
        end)
    end)

    return entities
end

function StateGatherer.GetThreats(player, radius)
    radius = radius or 20
    local threats = {}

    local success = pcall(function()
        local player_pos = Vector3(player.Transform:GetWorldPosition())
        if not player_pos then
            return
        end

        local all_entities = TheSim:FindEntities(player_pos.x, player_pos.y, player_pos.z, radius, {"hostile"})
        if not all_entities then
            return
        end

        for _, entity in ipairs(all_entities) do
            if entity and entity ~= player and entity:IsValid() then
                local entity_pos = Vector3(entity.Transform:GetWorldPosition())
                if entity_pos then
                    local distance = math.sqrt((entity_pos.x - player_pos.x) ^ 2 + (entity_pos.z - player_pos.z) ^ 2)

                    table.insert(threats, {
                        name = entity.prefab or "unknown",
                        distance = math.ceil(distance * 10) / 10
                    })
                end
            end
        end
    end)

    return threats
end

return StateGatherer
