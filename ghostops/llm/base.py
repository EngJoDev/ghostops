"""
GhostOps - Base LLM Provider Interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in GhostOps."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates a text completion given user prompt and optional system prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider endpoint / credentials are reachable and valid."""
        pass
