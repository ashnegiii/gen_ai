from typing import Dict, List, Optional
import os

from utils.llm.ollama_provider import OllamaProvider


class QueryRewritingService:
    def __init__(self):
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = OllamaProvider(
            model_name="llama3",
            base_url=ollama_url
        )

    def rewrite_query(
        self,
        query: str,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, str]:

        prompt = self._build_prompt(query, chat_history)

        rewritten = self.llm.generate(
            system_prompt=(
                "You are a query rewriting component in a customer-support RAG system. "
                "Your task is to rewrite user input into a concise, standalone, "
                "FAQ-style search query suitable for retrieving help-center articles. "
                "Do NOT answer the question."
            ),
            user_prompt=prompt
        )

        return {
            "original_query": query,
            "cleaned_query": rewritten.strip()
        }

    def _build_prompt(
        self,
        query: str,
        chat_history: Optional[List[Dict]]
    ) -> str:
        history = ""
        if chat_history:
            history = "\n".join(
                f"{m['role'].capitalize()}: {m['content']}"
                for m in chat_history[-5:]
                if "role" in m and "content" in m
            )

        return f"""
Rewrite the user input into a concise, standalone FAQ-style search query.

Guidelines:
- Assume the user is a customer asking for help
- Resolve references using the conversation context
- Preserve the user's underlying problem or intent
- Remove politeness, filler, and emotional language
- Use neutral FAQ wording (e.g. "How do I...", "What is...", "Why does...")
- Do NOT include answers or explanations
- Output ONLY the rewritten query

Conversation history:
{history if history else "None"}

User query:
{query}

Rewritten query:
""".strip()
