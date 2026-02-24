--[[
    JSON Utilities
    
    Simple table-to-JSON converter (no external dependencies)
]] --
local JSONUtils = {}

function JSONUtils.Encode(tbl)
    local success, result = pcall(function()
        return JSONUtils._EncodeValue(tbl)
    end)

    if success then
        return result
    else
        -- Fallback for encoding errors
        return "{}"
    end
end

function JSONUtils._EncodeValue(tbl)
    if type(tbl) == "string" then
        return '"' .. tbl:gsub('"', '\\"') .. '"'
    elseif type(tbl) == "number" then
        return tostring(tbl)
    elseif type(tbl) == "boolean" then
        return tbl and "true" or "false"
    elseif type(tbl) == "nil" then
        return "null"
    elseif type(tbl) == "table" then
        local is_array = true
        local last_index = 0
        for k, v in pairs(tbl) do
            if type(k) ~= "number" then
                is_array = false
                break
            end
            if k > last_index then
                last_index = k
            end
        end

        -- Check if it's a dense array
        if is_array and last_index == #tbl then
            local result = "["
            for i, v in ipairs(tbl) do
                if i > 1 then
                    result = result .. ","
                end
                result = result .. JSONUtils._EncodeValue(v)
            end
            return result .. "]"
        else
            -- Object
            local result = "{"
            local first = true
            for k, v in pairs(tbl) do
                if not first then
                    result = result .. ","
                end
                result = result .. '"' .. tostring(k) .. '":' .. JSONUtils._EncodeValue(v)
                first = false
            end
            return result .. "}"
        end
    else
        return "null"
    end
end

return JSONUtils
