# LLM Agent

The Python autonomous agent that controls the Don't Starve AI via LLM reasoning.

## Overview

This is the decision-making component of DST-AI. It:

1. **Monitors game state** from JSON file
2. **Prepares LLM prompts** with game context + memory
3. **Calls Ollama API** for LLM inference
4. **Executes actions** via JSON command file

## Installation

### Prerequisites

- Python 3.13+
- Ollama (https://ollama.ai)
- A Don't Starve world with the mod enabled and AI activated (Ctrl+P)

### Setup

```bash
# 1. Install Python dependencies
uv sync

# 2. Install Ollama model
ollama pull llama2
ollama pull gemma3:1b
# or: ollama pull mistral

# 3. Start Ollama server
ollama serve

# 4. In another terminal, start agent
uv run main.py --model llama2
```

## Architecture

```
1. Watch game_state.json
   ↓
2. Build prompt (state + memory + rules)
   ↓
3. Call Ollama API
   ↓
4. Parse JSON response
   ↓
5. Write action_command.json
   ↓
Game reads command → Wilson acts
```

## Memory System

The agent maintains memory of important events:

- **Decisions made** - What action was chosen and why
- **Events** - Combat, crafting, discoveries
- **Observations** - Threats, resources found
- **World resets** - Detected automatically

Memory is persisted in `state/agent_memory.jsonl` and included in every prompt.

## Actions Supported

The agent can command:

| Category  | Actions                            |
| --------- | ---------------------------------- |
| Movement  | move_to_food, explore              |
| Gathering | chop_tree, mine_rock, pick_up_item |
| Crafting  | craft_item:<recipe_name>           |
| Survival  | eat_food, cook_food                |
| Combat    | attack_enemy, run_from_enemy       |
| Idle      | idle                               |

## Emergency Handling

The agent automatically:

- Forces eating when health is low
- Flees from nearby threats
- Seeks light when dusk/night approaching
- Adapts to seasonal changes

## How It Works

1. **State Monitoring:** Polls `game_state.json` every 5 seconds
2. **Prompt Building:** Creates detailed context from state + memory
3. **LLM Reasoning:** Sends prompt to Ollama for inference
4. **Action Parsing:** Extracts JSON action from LLM response
5. **Command Write:** Saves action to `action_command.json`
6. **Memory Update:** Logs decision to persistent memory
7. **Repeat:** Waits for next decision window

## License

Built on "Artificial Wilson" mod by KingofTown.  
LLM integration and agent: Public domain / MIT
