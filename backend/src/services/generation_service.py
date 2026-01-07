# TODO Moritz: Implement methods for generation
import os
from backend.src.utils.llm.ollama_provider import OllamaProvider
from .prompt.prompts_library import RAGPrompts

class GenerationService:
    def __init__(self):
        # TODO put config in a config file later.
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm_provider = OllamaProvider(model_name="llama3", base_url=ollama_url)

    def generate_response_stream(self, query: str, retrieved_chunks: list):
        """
        Returns a generator that yields the response tokens one by one.
        """
        # Prepare the prompt
        context_text_list = retrieved_chunks # chunks as a list of strings

        system_instruction = RAGPrompts.SYSTEM_PROMPT_INSTRUCTED_GENERATION

        formatted_prompt = RAGPrompts.format_main_prompt(context_text_list, query)

        print(f"DEBUG PROMPT:\n{formatted_prompt}\n--- END OF PROMPT ---\n")

        # return the generator from the provider to stream the response
        return self.llm_provider.generate_stream(
            system_prompt=system_instruction,
            user_prompt=formatted_prompt
        )