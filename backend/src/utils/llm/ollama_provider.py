# src/utils/llm/ollama_provider.py
import requests
import json
from typing import Generator
from .base import LLMProvider
import logging

# Configure logging
logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
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
                "temperature": 0.1
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
                            self._log_metrics(data)
                            break

                        yield token

        except requests.exceptions.ConnectionError:
            yield "Error: No connection to Ollama server. Please ensure the Ollama service is running and accessible."
        except Exception as e:
            yield f"Unexpected error occurred: {str(e)}"


    def _log_metrics(self, data: dict) -> None:
        # Prompt evaluation metrics
        prompt_eval_count = data.get("prompt_eval_count", 0)
        prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)

        prompt_eval_sec = prompt_eval_duration_ns / 1_000_000_000  # convert ns to seconds

        # read tokens per second
        rtps = 0
        if prompt_eval_sec > 0:
            rtps = prompt_eval_count / prompt_eval_sec

        # Response Generation Evaluation
        eval_count = data.get("eval_count", 0)
        eval_duration_ns = data.get("eval_duration", 0)
        eval_sec = eval_duration_ns / 1_000_000_000

        # generated tokens per second
        tps = 0
        if eval_sec > 0:
            tps = eval_count / eval_sec

        # total answer time
        # 4. Response Generation (Das "Schreiben" der Antwort)
        total_duration_ns = data.get("total_duration", 0)
        total_sec = total_duration_ns / 1_000_000_000

        logger.info(f"Ollama Metrics - Total response time: {total_sec:.2f}s")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Prompt Reading: {prompt_eval_count} tokens in {prompt_eval_sec:.2f}s ({rtps:.2f} tokens/s)")
            logger.debug(f"Generation: {eval_count} tokens in {eval_sec:.2f}s ({tps:.2f} tokens/s)")
