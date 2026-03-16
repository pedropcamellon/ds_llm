"""utils/parsing.py — Generic parsing utilities for LLM responses."""

import re
import logging
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def parse_numbered_choice(response: str, options: list[T]) -> T | None:
    """Parse numbered choice from LLM response (expects "1", "2", "3", etc).

    Generic function that extracts a 1-indexed number from LLM output and
    returns the corresponding item from the options list.

    Args:
        response: Raw LLM output (expects "1", "2", "3", etc.)
        options: List of available options to choose from

    Returns:
        Selected option if valid, None if parsing fails or options is empty

    Examples:
        >>> colors = ["red", "green", "blue"]
        >>> parse_numbered_choice("2", colors)  # Returns "green"
        >>> parse_numbered_choice("1", colors)  # Returns "red"
        >>> parse_numbered_choice("5", colors)  # Returns None (out of range)
        >>> parse_numbered_choice("two", colors)  # Returns None (not a number)
        >>> parse_numbered_choice("2. Green item", colors)  # Returns "green" (extracts digit)
    """
    if not options:
        logger.warning("No options available for parsing")
        return None

    # Try direct integer parse
    try:
        choice = int(response.strip())
        if 1 <= choice <= len(options):
            logger.info(f"Selected option {choice} from {len(options)} choices")
            return options[choice - 1]  # 1-indexed → 0-indexed
        else:
            logger.warning(f"Choice {choice} out of range [1-{len(options)}]")
            return None
    except ValueError:
        pass  # Try regex extraction

    # Try extracting first digit from response (handles "1. Build base" format)
    match = re.search(r"\d+", response)
    if not match:
        logger.warning(
            f"Could not parse numbered choice from '{response}' (expected 1-{len(options)})"
        )
        return

    choice = int(match.group())
    if 1 <= choice <= len(options):
        logger.debug(f"Extracted choice {choice} from '{response}'")
        return options[choice - 1]

    logger.warning(
        f"Extracted {choice} from '{response}' but out of range [1-{len(options)}]"
    )
