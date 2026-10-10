"""
GhostOps - Local Ollama LLM Provider (100% Offline & Private).
"""

import requests
from typing import Optional
from ghostops.llm.base import BaseLLMProvider
from ghostops.config import config

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or config.get("llm", "model", "llama3:latest")
        self.base_url = (base_url or config.get("llm", "base_url", "http://localhost:11434")).rstrip("/")

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/api/version", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Sends generation request to Ollama endpoint."""
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
        }
        
        try:
            resp = requests.post(endpoint, json=payload, timeout=config.get("llm", "timeout", 45))
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "")
            else:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running (`ollama serve`) or switch to Gemini with `ghostops config --provider gemini`."
            )
