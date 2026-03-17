# AI Agent

This folder contains the external Python-side decision layer for the Don't Starve mod.

It is responsible for reading exported game state, maintaining agent-side memory, evaluating rule-based logic, building prompts, calling Ollama running locally, and selecting or scaffolding higher-level decisions.

## Current Scope

The current implementation is centered on high-level decision support, not full autonomous control.

Today, the Python agent primarily provides:

1. State ingestion from the shared `state/` folder
2. Inventory and world-change tracking across ticks
3. Emergency survival overrides for critical situations
4. Long-term and mid-term goal generation
5. LLM-assisted mid-term goal selection through a locally running Ollama instance

The full low-level action-selection and execution loop is only partially wired at the moment. Some action-planning and action-writing pieces exist in this folder, but the currently active path is focused on goal assistance first.

## Architecture

At a high level, the system works like this:

1. The Don't Starve mod exports world and player state into `state/game_state.json`.
2. The Python agent polls that state file on an interval.
3. The agent validates the snapshot and detects resets, death, inventory changes, and world-history changes.
4. Rule-based logic handles immediate emergencies such as low health, nearby threats, or darkness.
5. If no emergency override is needed, the goal system derives long-term context and a small set of mid-term options.
6. A prompt is built from state, memory, and goal options.
7. Ollama running locally is asked to choose the most appropriate mid-term goal.
8. The selected goal is stored as active agent context for later decisions.

In other words, the current Python agent is best understood as a state reader plus survival rules plus goal-selection engine, with the LLM currently helping at the mid-term planning layer.

## Main Runtime Components

- `main.py`: CLI entrypoint and dependency wiring
- `llm_agent.py`: Main orchestrator and decision loop
- `state_reader.py`: Reads and validates the exported game state
- `memory.py`: Persistent agent memory stored in JSONL format
- `inventory_tracker.py`: Tracks inventory snapshots and deltas
- `world_tracker.py`: Tracks recently seen world context across ticks
- `goals/`: Long-term, mid-term, and short-term goal logic
- `prompt/`: Prompt construction for LLM-facing context
- `ollama_client.py`: Local Ollama HTTP client
- `action_writer.py`: Command-file output for future or partial execution paths

## Shared Files

The Python agent communicates with the mod through the shared `state/` directory at the repository root.

Important files include:

- `state/game_state.json`: exported game snapshot from Lua
- `state/action_command.json`: command output channel for the mod
- `state/agent_memory.jsonl`: persistent agent-side memory log
- `state/conversation_log.jsonl`: prompt and response trace log

## Installation

### Prerequisites

- Python 3.13
- Ollama
- A Don't Starve world with the mod enabled

### Setup

```bash
# 1. Install Python dependencies
uv sync

# 2. Install Ollama model
ollama pull llama2
ollama pull gemma3:1b # very lightweight, good for testing
# or: ollama pull mistral

# 3. Start Ollama
ollama run llama2

# 4. Start the Python agent
uv run main.py --verbose
```

By default the agent connects to `http://localhost:11434`.

## Current Decision Loop

Each tick, the active loop in `llm_agent.py` does the following:

1. Read the latest game state
2. Detect death or world reset and clear stale state when needed
3. Update memory-facing trackers such as inventory and world history
4. Apply emergency overrides first
5. Re-evaluate the active mid-term goal or select a new one
6. Persist the selected goal and reasoning into memory
7. Wait for the next interval

That means the current live path is goal-centric rather than action-centric.

## Emergency Handling

Before asking the LLM anything, the agent can immediately react to critical situations such as:

- Very low health
- Nearby hostile threats
- Darkness or missing light
- World reset or player death

This keeps the safety-critical layer rule-based and fast.

## Notes On Future Integration

This folder already contains pieces for deeper execution, including action parsing, action planning, and command writing. The intended direction is to connect those parts more tightly so high-level goals can drive concrete actions with less manual scaffolding.
