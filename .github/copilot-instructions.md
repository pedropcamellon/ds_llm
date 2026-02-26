# Copilot Instructions — ds_llm (Artificial Wilson LLM Mod)

## Project Overview

Hybrid Don't Starve mod that combines a **Lua behavior-tree** (fast, rule-based)
with an **external Python/Ollama LLM agent** (slow, reasoning-based) for autonomous
Wilson gameplay. Communication is entirely via JSON files on disk — no sockets.

## Architecture: Two Processes, One Game

```
DS Game process (Lua)                Python Agent process
─────────────────────                ─────────────────────
llm_state_exporter  ──game_state.json──►  llm_agent.py
                                              │ build_prompt() [prompt.py]
                                              │ call Ollama API
llm_action_executor ◄─action_command.json──  │ parse JSON response
```

- **State export**: `scripts/components/llm_state_exporter.lua` (orchestrator)
  delegates to `state_gatherer.lua`, `memory_logger.lua`, `json_utils.lua`
- **Action import**: `scripts/components/llm_action_executor.lua` (polls for commands)
- **Python agent**: `agent/llm_agent.py` (I/O + decisions), `agent/prompt.py` (prompt text only), `agent/main.py` (CLI entrypoint)

## Critical Lua Rules (Don't Starve single-player)

- Always use `GLOBAL.require` in `modmain.lua`; use plain `require` inside components/brains.
- Wrap everything in `pcall` — exceptions crash the game silently.
- No `os.execute`. File I/O uses `io.open` with a path relative to the game executable
  (`D:\Games\Dont Starve v429404\`), e.g. `"../mods/ds_llm/state/game_state.json"`.
- **Do NOT use `TheSim:SetPersistentString` for state bridge files.** `TheSim` writes to
  `%USERPROFILE%\Documents\Klei\DoNotStarve\` which is a different directory from the mod
  folder — the Python agent cannot reliably locate it across machines. `io.open` + a
  mod-relative path is the proven working approach.
- Inventory iteration: use `player.components.inventory.itemslots` (DS single-player).
  `FindAllItems` is DST-only. Stack count = `item.components.stackable.stacksize or 1`.
- Components attach via `AddPrefabPostInit("wilson", fn)`, NOT `AddPlayerPostInit`.
- Debug output goes to `\Documents\Klei\DoNotStarve\log.txt` via `print()`.

## JSON State Contract

`state/game_state.json` fields the LLM prompt depends on:
```json
{ "day", "time_of_day", "season", "health", "hunger", "sanity",
  "inventory": ["log x20", "axe"],   ← prefab + stack count
  "equipped", "position": {"x","z"},
  "nearby_entities": [{"name","type","distance"}],
  "threats": [...],
  "speech_log": ["Take that, nature!", "I don't have the right tools."],
  "action_log": [{"result":"failed","action":"chop","reason":"no axe"}],
  "memory_log" }
```
`speech_log` and `action_log` are **accumulator buffers** — all events since the last export
are collected in Lua lists and flushed into the JSON each cycle, then cleared. This ensures
no transient event (speech bubble, action result) is lost between 5-second export intervals.

## State File Path

Both processes share the `state/` folder inside the mod directory:

| Side | Path |
|------|------|
| Lua (write) | `io.open("../mods/ds_llm/state/game_state.json", "w")` — relative to game exe |
| Python (read) | `Path(__file__).resolve().parent.parent / "state"` — relative to `agent/` via `__file__` |

`io.open` paths are relative to the game executable (`D:\Games\Dont Starve v429404\`).
The `../mods/ds_llm/state/` convention works as long as the mod is installed in the
standard `mods/` subfolder. `__file__`-relative resolution on the Python side means the
agent finds the correct folder regardless of the working directory it is launched from.

**Why not `TheSim:SetPersistentString`?** It writes to `%USERPROFILE%\Documents\Klei\DoNotStarve\`
— a different tree from the mod folder. Routing both sides through it would require
the Python agent to hardcode a Windows-only, user-specific Documents path, which breaks
across machines and Linux/Steam-Deck installs.

## BT ↔ LLM Handoff

The behavior tree (Lua) **always runs**. The LLM runs in parallel as a
verification/audit layer — it reads the same game state and can override
or confirm the BT's current action via `action_command.json`.

- BT handles low-level execution (pathfinding, animations, tool use).
- LLM handles high-level goal selection (what to do next, planning).
- Emergency overrides (health < 20, threats, nightfall) are hardcoded in
  `DSAIAgent.decide()` and fire **before** the LLM call to keep latency low.
- `llm_action_executor.lua` polling / dispatch is **not yet implemented**.

## Python Agent Conventions

- `agent/main.py` — CLI entrypoint only (argparse → `DSAIAgent.run()`)
- `agent/llm_agent.py` — all I/O, state hashing, emergency overrides, Ollama calls
- `agent/prompt.py` — pure prompt building: `build_prompt(state, memory) -> str`
  and `ACTION_SPACE`, `SYSTEM_RULES` constants. Edit here to tune LLM behaviour.
- Run with: `cd agent && uv run main.py --model gemma3:1b --interval 5`
- HTTP calls use `httpx` (not `requests`). Exceptions: `httpx.TimeoutException`, `httpx.ConnectError`, `httpx.HTTPError`.
- Type hints use built-in generics (`dict`, `list[dict]`, `str | None`) — no `typing.Dict/List/Optional`.
- Use **`dataclasses`** for internal data structures passed between agent modules (e.g. parsed action, state snapshot).
- Use **`pydantic`** for validating data from risky/external sources: Ollama API responses, `game_state.json` reads, `action_command.json` writes. Pydantic gives clear field-level errors and safe defaults when the LLM or Lua produces malformed output.
- Emergency hard-coded overrides (health < 20, threats, nightfall) fire **before**
  the LLM is called — keep fast-path logic in `DSAIAgent.decide()`, not in the prompt.

## Key File Map

| Path                                         | Role                                                   |
| -------------------------------------------- | ------------------------------------------------------ |
| `modmain.lua`                                | Hook registration, HUD pulse, keyboard toggle (Ctrl+P) |
| `scripts/brains/artificalwilson.lua`         | Behavior-tree brain (894 lines)                        |
| `scripts/behaviours/*.lua`                   | Individual BT leaf nodes                               |
| `scripts/components/llm_state_exporter.lua`  | Periodic JSON state writer                             |
| `scripts/components/state_gatherer.lua`      | Reads vitals, inventory, nearby ents                   |
| `scripts/components/llm_action_executor.lua` | Polls & dispatches action commands                     |
| `agent/prompt.py`                            | All LLM prompt text — tune here                        |
| `agent/llm_agent.py`                         | Agent core: state polling, Ollama, memory              |
| `state/game_state.json`                      | Live bridge file (Lua writes, Python reads)            |
| `state/action_command.json`                  | Live bridge file (Python writes, Lua reads)            |
| `mod_api_docs/`                              | Offline DS modding API reference                       |

## Component Skeleton Pattern (Lua)

```lua
local MyComponent = Class(function(self, inst)
    self.inst = inst
    self.inst:StartUpdatingComponent(self)
end)
function MyComponent:OnUpdate(dt) end
function MyComponent:OnSave() return {} end
function MyComponent:OnLoad(data) end
return MyComponent
```

## Active TODOs

- [ ] Set current season in `state_gatherer.lua`
- [ ] Implement `llm_action_executor.lua` action dispatcher
- [ ] Add `llm_action_executor` component to player in `modmain.lua`
