# src/utils/llm/ollama_provider.py
import requests
import json
from typing import Generator
from .base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://ollama:11434"):
        """
        Args:
            model_name: name of the model
            base_url: url to the ollama service
                      ollama in docker: usually 'http://ollama:11434'
                      locally: probably 'http://localhost:11434'.
        """
        self.model_name = model_name
        self.base_url = base_url

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True,
            "options": {
                "temperature": 0.3
            }
        }

        try:
            # stream=True keeps connection open for streaming
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()

                # iterate the lines as they arrive
                for line in response.iter_lines():
                    if line:
                        # lines from ollama
                        decoded_line = line.decode('utf-8')
                        data = json.loads(decoded_line)

                        # extract the token from the response
                        token = data.get("message", {}).get("content", "")

                        # stop if done
                        if data.get("done", False):
                            break

                        yield token

        except requests.exceptions.ConnectionError:
            yield "Error: No connection to Ollama server. Please ensure the Ollama service is running and accessible."
        except Exception as e:
            yield f"Unexpected error occurred: {str(e)}"