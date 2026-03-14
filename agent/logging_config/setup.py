"""Centralized logging setup for agent entry points."""

import logging


def configure_logging(verbose: bool = False) -> None:
    """Configure logging for agent and dependencies."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Keep app logs verbose, but suppress transport-level debug noise.
    for noisy_logger in ("httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
