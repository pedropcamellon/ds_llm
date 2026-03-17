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
    return None


def parse_goal_choice(response: str, goals: list[T]) -> tuple[T, str] | tuple[None, None]:
    """Parse goal choice with reason from LLM response.
    
    Expects response format: "<number> - <reason>" or "<number> because <reason>"
    
    Args:
        response: Raw LLM output (e.g., "2 - Need to prepare for winter")
        goals: List of available goal options
    
    Returns:
        Tuple of (selected_goal, reason) if valid, (None, None) if parsing fails
    
    Examples:
        >>> goals = [goal1, goal2, goal3]
        >>> parse_goal_choice("2 - Winter is coming", goals)
        (goal2, "Winter is coming")
        >>> parse_goal_choice("1 because low on food", goals)
        (goal1, "low on food")
        >>> parse_goal_choice("3: Need to explore", goals)
        (goal3, "Need to explore")
    """
    if not goals:
        logger.warning("No goals available for parsing")
        return None, None
    
    # Extract number (first digit sequence)
    num_match = re.search(r"(\d+)", response)
    if not num_match:
        logger.warning(f"Could not find goal number in '{response}'")
        return None, None
    
    choice = int(num_match.group(1))
    if not (1 <= choice <= len(goals)):
        logger.warning(f"Goal number {choice} out of range [1-{len(goals)}]")
        return None, None
    
    selected_goal = goals[choice - 1]
    
    # Extract reason (text after separator: -, because, :, etc.)
    reason_match = re.search(r"(?:\d+)\s*(?:-|because|:|–|—)\s*(.+)", response, re.IGNORECASE)
    if reason_match:
        reason = reason_match.group(1).strip()
        logger.info(f"Selected goal {choice}: {reason}")
        return selected_goal, reason
    
    # No reason found - just return the goal with empty reason
    logger.warning(f"Selected goal {choice} but no reason provided in '{response}'")
    return selected_goal, ""
