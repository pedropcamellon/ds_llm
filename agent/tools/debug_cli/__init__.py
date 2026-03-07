"""
debug_cli — Offline debug tool for agent pipeline testing.

A modular CLI tool for loading game state snapshots and running the full
agent pipeline (parsing → goals → actions → prompt) without running the game.

Architecture:
- cli.py: Argument parsing and orchestration
- pipeline.py: Executes agent modules in sequence
- state_loader.py: Loads/validates JSON files
- llm_client.py: Calls Ollama (optional)
- formatters/: Different output formats (JSON, text, actions-only, etc.)

Usage:
    python -m tools.debug_cli fixtures/low_health_hostile.json
    python -m tools.debug_cli state.json --actions-only
    python -m tools.debug_cli state.json --with-llm
"""

from .cli import main

__all__ = ["main"]
