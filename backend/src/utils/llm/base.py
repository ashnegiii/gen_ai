from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    """
    abstract interface for llm-provider.
    """

    @abstractmethod
    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        """
        Generates a response token by token (streams the response)

        Returns:
            A Generator that yields tokens piece by piece.
        """
        pass

    # Optional method for non-streaming generation
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        full_response = ""
        for chunk in self.generate_stream(system_prompt, user_prompt):
            full_response += chunk
        return full_response