"""
ollama_client.py — HTTP client for the local Ollama inference API.
"""

import httpx


class OllamaClient:
    def __init__(
        self,
        model: str = "llama2",
        url: str = "http://localhost:11434",
        temperature: float = 0.7,
        top_p: float = 0.95,
        timeout: float = 60.0,
    ):
        self.model = model
        self.url = url
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout

    def is_available(self) -> bool:
        """Return True if the Ollama server is reachable."""
        try:
            httpx.head(self.url, timeout=2)
            return True
        except httpx.HTTPError:
            return False

    def generate(self, prompt: str) -> str | None:
        """Send prompt to Ollama and return the raw text response, or None on failure."""
        if not self.is_available():
            print(f"[OllamaClient] Cannot reach Ollama at {self.url}")
            return None

        print(f"[OllamaClient] Calling {self.model}...")
        try:
            response = httpx.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                },
                timeout=self.timeout,
            )
            if response.status_code != 200:
                print(f"[OllamaClient] HTTP {response.status_code}")
                return None
            return response.json().get("response", "")
        except httpx.TimeoutException:
            print("[OllamaClient] Timeout — LLM took too long")
            return None
        except httpx.ConnectError:
            print(f"[OllamaClient] Connection refused at {self.url}")
            return None
        except Exception as e:
            print(f"[OllamaClient] Error: {e}")
            return None
