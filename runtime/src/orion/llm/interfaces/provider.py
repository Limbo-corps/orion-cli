from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class LLMProvider(ABC):
    """
    Abstract provider for creating LangChain chat models.
    """

    @abstractmethod
    def create(self) -> BaseChatModel:
        """
        Create and return the configured chat model.
        """
        raise NotImplementedError
