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

| Side          | Path                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------- |
| Lua (write)   | `io.open("../mods/ds_llm/state/game_state.json", "w")` — relative to game exe            |
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


## Rules

- **Never use `state.get(key) or default` for critical fields.**
  - Always extract required fields with a strict helper (see `goal_manager.py: _require_field`).
  - If a required field is missing or None, raise an error, emit an idle/pause action, and warn the user to check the Lua exporter.
  - Silent defaults (e.g. `health = state.get("health") or 100`) are dangerous: they can mask exporter bugs and cause the agent to act on wrong data.
- Type hints use built-in generics (`dict`, `list[dict]`, `str | None`) — no `typing.Dict/List/Optional`.
- Use **`dataclasses`** for internal data structures passed between agent modules (e.g. parsed action, state snapshot).
- Use **`pydantic`** for validating data from risky/external sources: Ollama API responses, `game_state.json` reads, `action_command.json` writes. Pydantic gives clear field-level errors and safe defaults when the LLM or Lua produces malformed output.
