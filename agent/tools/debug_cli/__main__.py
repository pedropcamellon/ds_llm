"""
__main__.py — Entry point for debug CLI module.

Allows running via: python -m tools.debug_cli
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
