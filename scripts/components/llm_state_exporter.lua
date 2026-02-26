--[[
    LLM State Exporter Component
    
    Main orchestrator that exports game state to JSON every N seconds.
    Delegates to specialized modules:
    - state_gatherer.lua: collects game state
    - memory_logger.lua: tracks events
    - json_utils.lua: JSON serialization
]] --
local StateGatherer = require "components/state_gatherer"
local MemoryLogger = require "components/memory_logger"
local JSONUtils = require "components/json_utils"

local LLMStateExporter = Class(function(self, inst)
    self.inst = inst
    self.export_interval = 5.0 -- Export state every n seconds
    self.last_export_time = 0
    self.state_dir = "../mods/ds_llm/state"
    self.state_file = self.state_dir .. "/game_state.json"
    self.memory_file = self.state_dir .. "/game_memory.json"

    print("[LLMStateExporter] Initializing...")
    print("[LLMStateExporter] State dir: " .. self.state_dir)
    print("[LLMStateExporter] State file: " .. self.state_file)

    -- Initialize sub-modules
    self.memory = MemoryLogger(self.memory_file, 20)

    -- Transient event buffers — accumulate between exports, flushed each cycle
    self.pending_speech   = {}  -- speech bubbles since last export
    self.pending_actions  = {}  -- action results since last export

    -- Register for updates
    self.inst:StartUpdatingComponent(self)
    print("[LLMStateExporter] Component registered for updates")

    -- Hook talker component for real game feedback (speech bubbles)
    -- ontalk fires before each Say() call with the raw script string
    pcall(function()
        if self.inst.components.talker then
            local orig_ontalk = self.inst.components.talker.ontalk
            self.inst.components.talker.ontalk = function(talker_inst, script)
                -- Wrap in pcall so any error here never aborts Say() / kills the speech bubble
                pcall(function()
                    local text = ""
                    if type(script) == "string" then
                        text = script
                    elseif type(script) == "table" and script[1] then
                        text = script[1].message or ""
                    end
                    if text ~= "" then
                        table.insert(self.pending_speech, text)
                        self.memory:Add("Wilson said: " .. text)
                    end
                end)
                if orig_ontalk then orig_ontalk(talker_inst, script) end
            end
            print("[LLMStateExporter] talker.ontalk hooked")
        else
            print("[LLMStateExporter] WARNING: talker component not found yet")
        end
    end)

    -- Listen for important events
    self.inst:ListenForEvent("actionsuccess", function(inst, data)
        self:OnActionSuccess(data)
    end)
    self.inst:ListenForEvent("actionfailed", function(inst, data)
        self:OnActionFailed(data)
    end)
    self.inst:ListenForEvent("attacked", function(inst, data)
        self:OnAttacked(data)
    end)
    self.inst:ListenForEvent("buildstructure", function(inst, data)
        self:OnBuilt(data)
    end)
    self.inst:ListenForEvent("builditem", function(inst, data)
        self:OnBuilt(data)
    end)
end)

-- Event handlers
function LLMStateExporter:OnActionSuccess(data)
    local success = pcall(function()
        if data and data.action then
            local entry = {result="success", action=tostring(data.action)}
            table.insert(self.pending_actions, entry)
            self.memory:Add("Action succeeded: " .. tostring(data.action))
        end
    end)
end

function LLMStateExporter:OnActionFailed(data)
    local success = pcall(function()
        if data and data.action then
            local entry = {result="failed", action=tostring(data.action), reason=data.reason or "unknown"}
            table.insert(self.pending_actions, entry)
            self.memory:Add("Action failed: " .. tostring(data.action))
        end
    end)
end

function LLMStateExporter:OnAttacked(data)
    local success = pcall(function()
        if data and data.attacker then
            self.memory:Add("Attacked by: " .. (data.attacker.prefab or "unknown"))
        end
    end)
end

function LLMStateExporter:OnBuilt(data)
    local success = pcall(function()
        if data and data.item then
            self.memory:Add("Built: " .. data.item.prefab)
        end
    end)
end

-- Main export function
function LLMStateExporter:ExportGameState()
    print("[LLMStateExporter] ExportGameState() called")
    local success, result = pcall(function()
        local clock = GetClock()
        local player = self.inst

        if not clock or not player then
            return
        end

        -- Gather all state using StateGatherer
        local day, time_of_day, season = StateGatherer.GetTimeInfo(clock)
        local health, hunger, sanity = StateGatherer.GetPlayerVitals(player)
        local inventory, equipped = StateGatherer.GetInventory(player)
        local position = StateGatherer.GetPosition(player)
        local nearby_entities = StateGatherer.GetNearbyEntities(player, 30)
        local threats = StateGatherer.GetThreats(player, 20)

        -- Build the state object
        local state = {
            day = day,
            time_of_day = math.ceil(time_of_day * 100) / 100,
            season = season,
            health = health,
            hunger = hunger,
            sanity = sanity,
            inventory = inventory,
            equipped = equipped,
            nearby_entities = nearby_entities,
            threats = threats,
            position = position,
            -- Flush transient buffers: all events since last export
            speech_log    = self.pending_speech,
            action_log    = self.pending_actions,
            memory_log    = self.memory:GetRecent(10)
        }
        -- Clear buffers after flushing into state
        self.pending_speech  = {}
        self.pending_actions = {}

        -- Write to JSON file using JSONUtils
        local json_str = JSONUtils.Encode(state)

        local f = io.open(self.state_file, "w")

        if f then
            f:write(json_str)
            f:close()
        else
            print("[ERROR] [LLMStateExporter] Failed to open: " .. self.state_file)
        end
    end)

    if not success then
        -- Silently fail - don't crash the game
        print("[ERROR] [LLMStateExporter] ExportGameState() error: " .. tostring(result))
    end
end

-- Update loop
function LLMStateExporter:OnUpdate(dt)
    local success = pcall(function()
        self.last_export_time = self.last_export_time + dt

        if self.last_export_time >= self.export_interval then
            self:ExportGameState()
            self.last_export_time = 0
        end
    end)

    if not success then
        -- Silently fail - don't crash the game
        print("[ERROR] [LLMStateExporter] OnUpdate() error: " .. tostring(result))
    end
end

-- Save/Load
function LLMStateExporter:OnSave()
    local success, result = pcall(function()
        return {
            memory_log = self.memory:GetLog()
        }
    end)

    if success then
        return result
    else
        print("[ERROR] [LLMStateExporter] OnSave error: " .. tostring(result))
        return {}
    end
end

function LLMStateExporter:OnLoad(data)
    local success = pcall(function()
        if data and data.memory_log then
            for _, entry in ipairs(data.memory_log) do
                self.memory.memory_log[#self.memory.memory_log + 1] = entry
            end
        end
    end)
end

return LLMStateExporter

