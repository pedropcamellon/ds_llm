# File I/O in Don't Starve Lua

> Important — DS runs in a sandboxed Lua 5.1. Most of `io.*` and `os.*` are
> restricted. The methods below are what actually works.

## `io.open` for mod-local files

Use `io.open` with paths **relative to the game executable**
(`D:\Games\Dont Starve v429404\`). This is the only reliable cross-platform
method for writing files that an external process (e.g. a Python agent in the
mod folder) can read.

```lua
-- Writing
local f = io.open("../mods/ds_llm/state/game_state.json", "w")
if f then
    f:write(json_string)
    f:close()
else
    print("[ERROR] Failed to open file for writing")
end

-- Reading
local f = io.open("../mods/ds_llm/state/game_state.json", "r")
if f then
    local contents = f:read("*a")
    f:close()
    local ok, data = pcall(json.decode, contents)
end
```

### Path convention

| Who writes | Path used | Physical location |
|---|---|---|
| Lua (`io.open`) | `"../mods/ds_llm/state/game_state.json"` | `<game_exe>/../mods/ds_llm/state/` |
| Python (`Path(__file__)`) | `Path(__file__).resolve().parent.parent / "state"` | Same folder |

Paths in `io.open` are relative to the game `.exe`, not the mod folder.
`../mods/ds_llm/` navigates from `<game_dir>/` up one level to `<game_dir>/../`
which is the parent of the game dir — so the full chain is:
`<game_dir>/../mods/ds_llm/state/`. Adjust if installation differs.

## ❌ Why NOT `TheSim:SetPersistentString`

`TheSim` writes to `%USERPROFILE%\Documents\Klei\DoNotStarve\` — a completely
different tree from the mod folder. An external Python agent cannot reliably
locate this path across machines or on Linux/Steam Deck.

```lua
-- DO NOT USE for inter-process bridge files
TheSim:SetPersistentString("key", data, false, callback)
TheSim:GetPersistentString("key", callback)
-- Writes to: %USERPROFILE%\Documents\Klei\DoNotStarve\<key>
```

Use `TheSim` only for game save data that never needs to be read outside the
DS process.

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
