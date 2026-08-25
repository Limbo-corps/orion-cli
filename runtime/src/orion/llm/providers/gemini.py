from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import override

from orion.llm.config import LLMConfig
from orion.llm.interfaces.provider import LLMProvider


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider.
    """

    def __init__(
        self,
        config: LLMConfig,
    ) -> None:
        self.config = config

    @override
    def create(self) -> BaseChatModel:
        if not self.config.gemini_api_key:
            raise ValueError(
                "Gemini API key not set"
            )

        if not self.config.model:
            raise ValueError(
                "Gemini model not set"
            )

        return ChatGoogleGenerativeAI(
            model=self.config.model,
            google_api_key=self.config.gemini_api_key,
        )
