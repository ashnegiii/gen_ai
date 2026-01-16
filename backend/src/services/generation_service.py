import os
from utils.llm.ollama_provider import OllamaProvider
from .prompt.prompts_library import RAGPrompts

class GenerationService:
    def __init__(self):
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm_provider = OllamaProvider(model_name="llama3", base_url=ollama_url)

    def _trim_chunks_to_fit_context(self, chunks: list[str], max_chars=20000)  -> list[str]:
        # 20000 = 8000 tokens (llama3 context window 819) * 2,5 chars per token (4 chars per token usual estimate)
        current_length = 0
        selected_chunks = []

        for chunk in chunks:
            # +3 for chunk separation "\n---\n"
            chunk_len = len(chunk) + 5

            if current_length + chunk_len > max_chars:
                print(f"DEBUG: Context limit reached via chunk trimming ({current_length}/{max_chars})")
                break

            selected_chunks.append(chunk)
            current_length += chunk_len

        return selected_chunks

    def generate_response_stream(self, query: str, retrieved_chunks: list):
        """
        Returns a generator that yields the response tokens one by one.
        """
        # Clean the chunks if necessary
        clean_chunks = []
        for chunk in retrieved_chunks:
            if isinstance(chunk, tuple) or isinstance(chunk, list):
                clean_chunks.append(chunk[0]) # Extract the string from the tuple/list
            else:
                clean_chunks.append(str(chunk)) # Ensure it's a string

        # prepare the prompt
        system_instruction = RAGPrompts.SYSTEM_PROMPT_INSTRUCTED_GENERATION

        final_chunks = self._trim_chunks_to_fit_context(clean_chunks)

        formatted_prompt = RAGPrompts.format_main_prompt(query, final_chunks)

        # return the generator from the provider to stream the response
        return self.llm_provider.generate_stream(
            system_prompt=system_instruction,
            user_prompt=formatted_prompt
        )