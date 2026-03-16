"""
cli.py — Command-line interface for debug tool.

Handles argument parsing and orchestrates pipeline execution with formatting.
"""

import argparse
import sys
from pathlib import Path

from .formatters import (
    JsonFormatter,
    PromptFormatter,
    TextFormatter,
)
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
            description="Debug tool: run agent as black box on a game state"
        )
        parser.add_argument("state_file", type=Path, help="Path to game_state.json")
        
        # Mode selection
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "--full", action="store_true", help="Run full decide() (default, respects phase throttling)"
        )
        mode_group.add_argument(
            "--llm", action="store_true", help="Force strategic LLM call (ignore throttling)"
        )
        mode_group.add_argument(
            "--goap", action="store_true", help="Force GOAP execution only (no LLM)"
        )
        
        parser.add_argument(
            "--goal", type=str, help="Goal to use with --goap mode (e.g., 'prepare_light')"
        )
        
        # Output formatters
        parser.add_argument(
            "--prompt-only", action="store_true", help="Show only the LLM prompt (if called)"
        )
        parser.add_argument(
            "--json", action="store_true", help="Output as machine-readable JSON"
        )
        parser.add_argument(
            "--model",
            default="gemma3:1b",
            help="Ollama model to use (default: gemma3:1b)",
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

            # Determine mode
            if parsed_args.llm:
                mode = "llm"
            elif parsed_args.goap:
                mode = "goap"
            else:
                mode = "full"

            # Run agent as black box
            pipeline = DebugPipeline(
                state_path=parsed_args.state_file,
                model=parsed_args.model
            )
            result = pipeline.run(state, mode=mode, force_goal=parsed_args.goal)

            # Select formatter based on flags
            formatter = self._select_formatter(parsed_args)

            # Format and print output
            output = formatter.format(result)
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
        elif args.prompt_only:
            return PromptFormatter()
        else:
            return TextFormatter()


def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    cli = DebugCli()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
