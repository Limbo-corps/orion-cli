from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from pydantic import SecretStr
from typing_extensions import override
from typing import cast

from orion.llm.config import LLMConfig
from orion.llm.interfaces.provider import LLMProvider


class GroqProvider(LLMProvider):
    """
    Groq LLM provider.
    """

    def __init__(
        self,
        config: LLMConfig,
    ) -> None:
        self.config = config

    @override
    def create(self) -> BaseChatModel:
        if not self.config.groq_api_key:
            raise ValueError(
                "Groq API key not set"
            )

        if not self.config.model:
            raise ValueError(
                "Groq model not set"
            )

        return ChatGroq(
            model=self.config.model,
            api_key=cast(SecretStr, self.config.groq_api_key),
        )
