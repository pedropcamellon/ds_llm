# Mod Structure

Source: https://dst-api-docs.fandom.com/wiki/Mod_Structure

> Not an exhaustive reference — covers the most essential parts.

## Core Files

Every mod has up to 3 entry-point scripts. Everything else (scripts, images,
sounds) can be placed freely — just use the correct path when referencing them.

| File | Purpose |
|------|---------|
| `modinfo.lua` | Metadata: name, description, author, compatibility, config options |
| `modmain.lua` | Main mod logic: hook into the game API, add components, patch behaviours |
| `modworldgenmain.lua` | World-generation overrides (optional, DST only) |

## Typical Folder Layout

```
mods/
  your_mod/
    modinfo.lua
    modmain.lua
    modicon.tex / modicon.xml   ← mod icon (optional)
    scripts/
      components/               ← custom components attached to entities
      brains/                   ← AI brain scripts
      behaviours/               ← individual behaviour-tree nodes
      prefabs/                  ← custom entity definitions
    images/                     ← atlases, textures
    anim/                       ← animation zips
    sound/                      ← FMOD bank files
    state/                      ← runtime data files (e.g. JSON for LLM bridge)
```

## Notes
- Paths in `Assets = {}` and `PrefabFiles = {}` are relative to the mod root.
- `GLOBAL.require` is used in `modmain.lua` to load scripts; plain `require`
  works inside component/brain files.
- All code runs in DS's sandboxed Lua 5.1 — many standard libraries are
  restricted (`os.execute`, `io.*`, etc.).
