"""
debug_cli.py — Convenience wrapper for tools.debug_cli module.

For backward compatibility. Run via:
    python debug_cli.py <state.json> [options]
or:
    python -m tools.debug_cli <state.json> [options]
    uv run debug_cli.py <state.json> [options]
"""

import sys

from tools.debug_cli import main

if __name__ == "__main__":
    sys.exit(main())
