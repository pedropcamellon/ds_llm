"""
llm_client.py — LLM interaction wrapper.

Handles calling Ollama and parsing responses.
"""

from action_parser import ActionParser
from ollama_client import OllamaClient


class LlmClient:
    """Wrapper for LLM calls with response parsing."""

    def __init__(self, model: str = "llama3.2:latest"):
        """Initialize with specified model."""
        self.model = model
        self.client = OllamaClient(model=model)
        self.parser = ActionParser()

    def call(self, prompt: str) -> dict:
        """
        Call Ollama with prompt and parse response.

        Returns dict with 'raw', 'action', and optionally 'error' keys.
        """
        try:
            raw_response = self.client.generate(prompt)
            # Handle None response from failed API call
            if raw_response is None:
                raw_response = ""
            action = self.parser.parse(raw_response)
            return {"raw": raw_response, "action": action}
        except Exception as e:
            return {"error": str(e), "raw": "", "action": {}}
