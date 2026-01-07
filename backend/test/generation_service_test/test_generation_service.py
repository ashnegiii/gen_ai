import unittest
import sys
import os

from backend.src.services.generation_service import GenerationService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


class TestGenerationService(unittest.TestCase):
    def setUp(self):
        self.service = GenerationService()

        self.service.llm_provider.base_url = "http://localhost:11434"  # assuming local ollama for tests

    def test_generation_service_stream_integration(self):
        query = "What is the capital of France?"
        chunks = [
            "France is a country in Europe.",
            "The capital of France is Paris.",
            "France is known for its culture and history."
        ]

        response_generator = self.service.generate_response_stream(query, chunks)

        full_answer = ""

        for token in response_generator:
            full_answer += token
            print(token, end="", flush=True)

        print("\n--- Test Completed ---")

        print("Full Answer:", full_answer)
        self.assertIsNotNone(full_answer)
        self.assertGreater(len(full_answer), 0, "The generated answer should not be empty.")
        self.assertIn("Paris", full_answer, "Das Modell sollte 'Paris' in der Antwort haben")

if __name__ == '__main__':
    unittest.main()