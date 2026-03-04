"""
__main__.py — Entry point for `python -m agent` or `uv run python -m agent`.

Routes to debug_cli by default for offline debugging.
"""

import sys
from debug_cli import main

if __name__ == "__main__":
    sys.exit(main())
