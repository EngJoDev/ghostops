"""
GhostOps - LLM Provider Factory.
"""

from ghostops.config import config
from ghostops.llm.base import BaseLLMProvider
from ghostops.llm.ollama import OllamaProvider
from ghostops.llm.gemini import GeminiProvider
from ghostops.llm.openai_compat import OpenAICompatProvider

def get_llm_provider() -> BaseLLMProvider:
    """
    Returns the active LLM provider based on user configuration.
    Defaults to Ollama or Gemini if keys are present.
    """
    provider_name = config.provider.lower()

    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name in ("openai", "groq", "openrouter"):
        return OpenAICompatProvider()
    else:
        # Default to Ollama
        return OllamaProvider()
