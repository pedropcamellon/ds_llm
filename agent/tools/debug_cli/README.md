# Debug CLI Tool

Offline debug tool for testing the agent decision pipeline without running the game.

## Overview

The debug CLI loads a game state snapshot (JSON), runs the complete agent pipeline, and displays the results in various formats. This is invaluable for testing changes to goals, action planning, or prompt generation.

## Architecture

- `DebugCli` depends on abstractions (`OutputFormatter`) not concrete classes
- `OutputFormatter` defines minimal interface: `format(result, llm_response)`
- Each formatter implements only what it needs
- Formatters are injected based on CLI flags
- Formatters implement `OutputFormatter` interface
- New formatters can be added without modifying existing code

Each module has one clear purpose:
- **cli.py** — Argument parsing and orchestration
- **pipeline.py** — Executes agent modules sequentially
- **state_loader.py** — File I/O for state snapshots
- **llm_client.py** — LLM interaction (optional)
- **formatters/** — Output formatting (Strategy pattern)

## Usage

```bash
# Basic usage
python -m tools.debug_cli fixtures/low_health_hostile.json

# Show only actions
python -m tools.debug_cli fixtures/low_health_hostile.json --actions-only

# Show only prompt
python -m tools.debug_cli fixtures/low_health_hostile.json --prompt-only

# JSON output (machine-readable)
python -m tools.debug_cli fixtures/low_health_hostile.json --json

# Actually call Ollama
python -m tools.debug_cli fixtures/low_health_hostile.json --with-llm

# Use different model
python -m tools.debug_cli fixtures/low_health_hostile.json --with-llm --model mistral:latest
```

## Module Structure

```
tools/debug_cli/
├── __init__.py          # Package exports
├── __main__.py          # Entry point (python -m)
├── cli.py               # CLI application class
├── pipeline.py          # Pipeline executor
├── state_loader.py      # JSON state loader
├── llm_client.py        # Ollama client wrapper
└── formatters/
    ├── __init__.py
    ├── base.py          # Abstract interface
    ├── json_formatter.py
    ├── text_formatter.py
    ├── actions_formatter.py
    └── prompt_formatter.py
```

## Adding New Formatters

1. Create new file in `formatters/`
2. Inherit from `OutputFormatter`
3. Implement `format(result, llm_response)` method
4. Export in `formatters/__init__.py`
5. Add CLI flag in `cli.py`

Example:

```python
# formatters/csv_formatter.py
from tools.debug_cli.formatters.base import OutputFormatter

class CsvFormatter(OutputFormatter):
    def format(self, result, llm_response=None):
        # Return CSV format
        pass
```

## Testing

Run tests from the agent directory:

```bash
pytest tests/test_debug_cli.py
```

## Design Patterns Used

- **Strategy Pattern**: Formatters (interchangeable output strategies)
- **Facade Pattern**: `DebugPipeline` (simplifies module orchestration)
- **Template Method**: `OutputFormatter` (defines format interface)
- **Dependency Injection**: Formatter selection based on CLI flags
