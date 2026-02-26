#!/usr/bin/env python3
"""
main.py — CLI entry point and dependency-injection wiring.

Usage:
    uv run main.py
    uv run main.py --model gemma3:1b --interval 8
"""

import argparse
from pathlib import Path

from action_parser import ActionParser
from action_writer import ActionWriter
from conversation_log import ConversationLog
from inventory_tracker import InventoryTracker
from llm_agent import DSAIAgent
from memory import AgentMemory
from ollama_client import OllamaClient
from state_reader import StateReader
from world_tracker import WorldTracker

STATE_DIR = Path(__file__).resolve().parent.parent / "state"


def main():
    parser = argparse.ArgumentParser(description="Run Don't Starve LLM Agent")
    parser.add_argument(
        "--model", default="llama2", help="Ollama model (default: llama2)"
    )
    parser.add_argument(
        "--url", default="http://localhost:11434", help="Ollama API URL"
    )
    parser.add_argument(
        "--interval", type=float, default=5.0, help="Poll interval in seconds"
    )
    args = parser.parse_args()

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    memory = AgentMemory(STATE_DIR / "agent_memory.jsonl")

    agent = DSAIAgent(
        state_reader=StateReader(STATE_DIR / "game_state.json"),
        memory=memory,
        llm_client=OllamaClient(model=args.model, url=args.url),
        action_parser=ActionParser(),
        action_writer=ActionWriter(STATE_DIR / "action_command.json"),
        inventory_tracker=InventoryTracker(memory),
        conversation_log=ConversationLog(STATE_DIR / "conversation_log.jsonl"),
        world_tracker=WorldTracker(ttl_seconds=120.0),
    )
    agent.run(interval=args.interval)


if __name__ == "__main__":
    main()
