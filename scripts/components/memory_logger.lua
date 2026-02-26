--[[
    Memory Logger
    
    Tracks important game events and logs them to disk.
]] --
local JSONUtils = require "components/json_utils"

local MemoryLogger = Class(function(self, memory_file, max_entries)
    self.memory_file = memory_file
    self.max_memory_entries = max_entries or 20
    self.memory_log = {}
    print("[MemoryLogger] Initialized with file: " .. memory_file)
    self:Load()
end)

function MemoryLogger:Load()
    local success, err = pcall(function()
        local f = io.open(self.memory_file, "r")
        if not f then
            print("[MemoryLogger] No existing memory file found")
            return
        end
        local count = 0
        for line in f:lines() do
            if line ~= "" then
                local ok, entry = pcall(json.decode, line)
                if ok and type(entry) == "table" then
                    table.insert(self.memory_log, entry)
                    count = count + 1
                end
            end
        end
        f:close()
        -- Trim to max entries
        while #self.memory_log > self.max_memory_entries do
            table.remove(self.memory_log, 1)
        end
        print("[MemoryLogger] Loaded " .. count .. " entries from " .. self.memory_file)
    end)
    if not success then
        print("[ERROR] [MemoryLogger] Load error: " .. tostring(err))
    end
end

function MemoryLogger:Add(text)
    local clock = GetClock()
    if not clock then
        print("[MemoryLogger] Add() failed: GetClock() is nil")
        return
    end

    local entry = {
        timestamp = clock:GetDayTime(),
        day = clock:GetDay(),
        text = text
    }

    table.insert(self.memory_log, entry)

    -- Keep only last N entries
    if #self.memory_log > self.max_memory_entries then
        table.remove(self.memory_log, 1)
    end

    -- Append to file
    local success = pcall(function()
        local f = io.open(self.memory_file, "a")
        if f then
            f:write(JSONUtils.Encode(entry) .. "\n")
            f:close()
        else
            print("[ERROR] [MemoryLogger] Failed to open: " .. self.memory_file)
        end
    end)
    if not success then
        print("[ERROR] [MemoryLogger] Write error - data still in RAM")
    end
end

function MemoryLogger:GetRecent(count)
    count = count or 10
    local result = {}
    local start_idx = math.max(1, #self.memory_log - (count - 1))
    for i = start_idx, #self.memory_log do
        table.insert(result, self.memory_log[i].text)
    end
    return result
end

function MemoryLogger:GetLog()
    return self.memory_log
end

return MemoryLogger
