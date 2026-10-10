"""
GhostOps - OpenAI Compatible LLM Provider.
"""

import os
import requests
from typing import Optional
from ghostops.llm.base import BaseLLMProvider
from ghostops.config import config

class OpenAICompatProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or config.api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or config.get("llm", "model", "gpt-4o-mini")
        self.base_url = (base_url or config.get("llm", "base_url", "https://api.openai.com/v1")).rstrip("/")

    def is_available(self) -> bool:
        """Returns True if API key or local base_url is configured."""
        return bool(self.api_key or "localhost" in self.base_url)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Sends generation request to OpenAI-compatible chat completions endpoint."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=config.get("llm", "timeout", 45))
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
            else:
                raise RuntimeError(f"OpenAI compatible API error (HTTP {resp.status_code}): {resp.text}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to communicate with API: {e}")
