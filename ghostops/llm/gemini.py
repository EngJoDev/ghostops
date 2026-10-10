"""
GhostOps - Google Gemini API Provider.
"""

import os
import requests
from typing import Optional
from ghostops.llm.base import BaseLLMProvider
from ghostops.config import config

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or config.get("llm", "model", "gemini-1.5-flash")

    def is_available(self) -> bool:
        """Returns True if Gemini API key is configured."""
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Sends generation request to Gemini REST API."""
        if not self.api_key:
            raise ValueError(
                "Gemini API key is not configured. "
                "Set it via `export GEMINI_API_KEY=your_key` or `ghostops config --api-key your_key`."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System Instructions:\n{system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will act as the Senior SRE GhostOps and provide precise structured analysis."}]
            })
            
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=config.get("llm", "timeout", 45))
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
            else:
                raise RuntimeError(f"Gemini API error (HTTP {resp.status_code}): {resp.text}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to communicate with Gemini API: {e}")
