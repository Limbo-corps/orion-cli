from dataclasses import dataclass, field
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class LLMConfig:
    """
    Configuration for the ORION language model.

    The provider determines which LangChain chat model is
    constructed by the LLM factory.
    """

    # ==========================================================
    # Provider
    # ==========================================================

    provider: str = field(
        default_factory=lambda: os.getenv(
            "ORION_LLM_PROVIDER",
            "gemini",
        )
    )

    # ==========================================================
    # Model
    # ==========================================================

    model: str = field(
        default_factory=lambda: os.getenv(
            "ORION_LLM_MODEL",
            "",
        )
    )

    # ==========================================================
    # API Keys
    # ==========================================================

    gemini_api_key: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_API_KEY",
            "",
        )
    )

    groq_api_key: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_API_KEY",
            "",
        )
    )
