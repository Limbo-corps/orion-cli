import pytest
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from orion.llm.config import LLMConfig
from orion.llm.providers.groq import GroqProvider


def test_create_groq() -> None:
    config = LLMConfig(
        provider="groq",
        model="openai/gpt-oss-120b",
        groq_api_key="test-groq-key",
    )

    provider = GroqProvider(config)

    llm = provider.create()

    assert isinstance(
        llm,
        BaseChatModel,
    )

    assert isinstance(
        llm,
        ChatGroq,
    )

    assert llm.model_name == "openai/gpt-oss-120b"


def test_create_groq_requires_api_key() -> None:
    config = LLMConfig(
        provider="groq",
        model="openai/gpt-oss-120b",
        groq_api_key="",
    )

    provider = GroqProvider(config)

    with pytest.raises(
        ValueError,
        match="Groq API key not set",
    ):
        provider.create()


def test_create_groq_requires_model() -> None:
    config = LLMConfig(
        provider="groq",
        model="",
        groq_api_key="test-groq-key",
    )

    provider = GroqProvider(config)

    with pytest.raises(
        ValueError,
        match="Groq model not set",
    ):
        provider.create()
