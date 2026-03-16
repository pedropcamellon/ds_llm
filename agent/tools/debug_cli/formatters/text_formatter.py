"""
text_formatter.py — Full text output formatter for agent black-box testing.
"""

import json

from .base import OutputFormatter, format_state_summary


class TextFormatter(OutputFormatter):
    """Formats agent decision results as human-readable text."""

    def format(self, result, llm_response: dict | None = None) -> str:
        """Format agent decision with context."""
        sections = []

        # State summary
        sections.append("=" * 80)
        sections.append("[STATE SUMMARY]")
        sections.append(format_state_summary(result.state))

        # Mode and goal
        sections.append("\n" + "=" * 80)
        sections.append(f"[AGENT MODE]: {result.mode}")

        # If LLM mode, show the full decision chain
        if result.llm_called:
            sections.append("\n[STRATEGIC LAYER - LLM]")
            if result.suggested_goals:
                sections.append("  Goals offered: " + ", ".join(result.suggested_goals))
            if result.current_goal:
                sections.append(f"  LLM chose: {result.current_goal}")
            if result.llm_reason:
                sections.append(f"  Reason: {result.llm_reason}")

        # GOAP chain (if available)
        if result.goap_chain:
            sections.append("\n[TACTICAL LAYER - GOAP]")
            sections.append(f"  Goal: {result.current_goal}")
            sections.append("  Plan: " + " → ".join(result.goap_chain))
        elif result.current_goal:
            sections.append(f"\n[CURRENT GOAL]: {result.current_goal}")

        # Action decision
        sections.append("\n" + "=" * 80)
        sections.append("[AGENT DECISION]")
        if result.action:
            sections.append(f"  Action: {result.action.get('action')}")
            if result.action.get('target'):
                sections.append(f"  Target: {result.action.get('target')}")
            sections.append(f"  Reason: {result.action.get('reason')}")
        else:
            sections.append("  (no action - state unchanged)")

        # Prompt (if LLM was called and verbose)
        if result.llm_called and result.prompt_text:
            sections.append("\n" + "=" * 80)
            sections.append("[LLM PROMPT]")
            sections.append(result.prompt_text)
            
            if llm_response:
                raw_response = llm_response.get("raw") or ""
                if raw_response:
                    sections.append(raw_response)

        return "\n".join(sections)
