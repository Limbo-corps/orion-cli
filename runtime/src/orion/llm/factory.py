from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from orion.llm.config import LLMConfig
from orion.llm.interfaces.provider import LLMProvider
from orion.llm.providers.gemini import GeminiProvider
from orion.llm.providers.groq import GroqProvider


@dataclass(slots=True)
class LLMProviders:
    """
    Container for LLM providers.
    """

    provider: LLMProvider


class LLMFactory:
    """
    Creates the configured LLM provider.
    """

    @staticmethod
    def create(
        config: LLMConfig,
    ) -> LLMProviders:

        if config.provider == "gemini":
            provider = GeminiProvider(config)

        elif config.provider == "groq":
            provider = GroqProvider(config)

        else:
            raise ValueError(
                f"Unsupported LLM provider: {config.provider}"
            )

        return LLMProviders(
            provider=provider,
        )
