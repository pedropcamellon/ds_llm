# File I/O in Don't Starve Lua

> Important — DS runs in a sandboxed Lua 5.1. Most of `io.*` and `os.*` are
> restricted. The methods below are what actually works.

## Reading a File

```lua
-- TheSim:GetPersistentString reads from the save directory
-- Path is relative to the Klei save folder, NOT the mod folder
TheSim:GetPersistentString("ds_llm/state/game_state.json", function(success, data)
    if success and data and data ~= "" then
        -- data is the raw file contents (string)
        local ok, decoded = pcall(json.decode, data)
        if ok then
            -- use decoded table
        end
    end
end)
```

## Writing a File

```lua
-- TheSim:SetPersistentString writes to the same directory
local encoded = json.encode(my_table)
TheSim:SetPersistentString("ds_llm/state/game_state.json", encoded, false, function()
    -- optional callback when write completes (may be async)
end)
```

## Actual Paths on Disk

| Lua path argument                | Windows physical path                                                   |
| -------------------------------- | ----------------------------------------------------------------------- |
| `"ds_llm/state/game_state.json"` | `%USERPROFILE%\Documents\Klei\DoNotStarve\ds_llm\state\game_state.json` |

> The Python agent reads/writes the same physical path. Make sure both sides
> agree on the exact filename.

## JSON Encoding/Decoding

DS ships a built-in `json` global:

```lua
local str   = json.encode(table)    -- table → JSON string
local tbl   = json.decode(str)      -- JSON string → table
```

Always wrap in `pcall` — malformed input will throw:

```lua
local ok, result = pcall(json.decode, raw_string)
if not ok then
    print("[error] JSON decode failed: " .. tostring(result))
end
```

## Periodic Polling Pattern

```lua
-- Poll action_command.json every 5 seconds
inst:DoPeriodicTask(5, function()
    TheSim:GetPersistentString("ds_llm/state/action_command.json", function(success, data)
        if not success or not data or data == "" then return end
        local ok, cmd = pcall(json.decode, data)
        if ok and cmd and cmd.action then
            DispatchAction(cmd.action)
        end
    end)
end)
```

## Known Limitations

- No synchronous file read — all reads are callbacks.
- No `io.open`, `os.execute`, or `os.rename`.
- Paths cannot go outside the Klei save directory.
- Write timing is not guaranteed to be immediate — always check the callback.

## TODO
- [ ] Confirm exact save path on macOS / Linux
- [ ] Handle file-not-found vs empty-file distinction
- [ ] Atomic write pattern (write to temp, rename) — may not be possible in sandbox
