import pytest
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from orion.llm.config import LLMConfig
from orion.llm.providers.gemini import GeminiProvider


def test_create_gemini() -> None:
    config = LLMConfig(
        provider="gemini",
        model="gemini-2.5-flash",
        gemini_api_key="test-gemini-key",
    )

    provider = GeminiProvider(config)

    llm = provider.create()

    assert isinstance(
        llm,
        BaseChatModel,
    )

    assert isinstance(
        llm,
        ChatGoogleGenerativeAI,
    )

    assert llm.model == "gemini-2.5-flash"


def test_create_gemini_requires_api_key() -> None:
    config = LLMConfig(
        provider="gemini",
        model="gemini-2.5-flash",
        gemini_api_key="",
    )

    provider = GeminiProvider(config)

    with pytest.raises(
        ValueError,
        match="Gemini API key not set",
    ):
        provider.create()


def test_create_gemini_requires_model() -> None:
    config = LLMConfig(
        provider="gemini",
        model="",
        gemini_api_key="test-gemini-key",
    )

    provider = GeminiProvider(config)

    with pytest.raises(
        ValueError,
        match="Gemini model not set",
    ):
        provider.create()
