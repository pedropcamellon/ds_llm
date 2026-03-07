"""
cli.py — Command-line interface for debug tool.

Handles argument parsing and orchestrates pipeline execution with formatting.
"""

import argparse
import sys
from pathlib import Path

from .formatters import (
    ActionsFormatter,
    JsonFormatter,
    PromptFormatter,
    TextFormatter,
)
from .llm_client import LlmClient
from .pipeline import DebugPipeline
from .state_loader import StateLoadError, StateLoader


class DebugCli:
    """Main CLI application."""

    def __init__(self):
        """Initialize CLI with argument parser."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all options."""
        parser = argparse.ArgumentParser(
            description="Debug tool: load game state and show decision pipeline"
        )
        parser.add_argument("state_file", type=Path, help="Path to game_state.json")
        parser.add_argument(
            "--actions-only", action="store_true", help="Show only action lists"
        )
        parser.add_argument(
            "--prompt-only", action="store_true", help="Show only the LLM prompt"
        )
        parser.add_argument(
            "--json", action="store_true", help="Output as machine-readable JSON"
        )
        parser.add_argument(
            "--with-llm",
            action="store_true",
            help="Actually call Ollama and show response",
        )
        parser.add_argument(
            "--model",
            default="llama3.2:latest",
            help="Ollama model to use (if --with-llm)",
        )
        return parser

    def run(self, args: list[str] | None = None) -> int:
        """
        Run the CLI application.

        Args:
            args: Command-line arguments (defaults to sys.argv)

        Returns:
            Exit code (0 = success, 1 = error)
        """
        parsed_args = self.parser.parse_args(args)

        try:
            # Load state
            state = StateLoader.load(parsed_args.state_file)

            # Run pipeline
            pipeline = DebugPipeline()
            result = pipeline.run(state)

            # Call LLM if requested
            llm_response = None
            if parsed_args.with_llm:
                llm_client = LlmClient(model=parsed_args.model)
                llm_response = llm_client.call(result.prompt_text)

            # Select formatter based on flags
            formatter = self._select_formatter(parsed_args)

            # Format and print output
            output = formatter.format(result, llm_response)
            print(output)

            return 0

        except StateLoadError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            return 1

    def _select_formatter(self, args):
        """Select appropriate formatter based on CLI flags."""
        if args.json:
            return JsonFormatter()
        elif args.actions_only:
            return ActionsFormatter()
        elif args.prompt_only:
            return PromptFormatter()
        else:
            return TextFormatter(max_actions=20)


def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    cli = DebugCli()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
