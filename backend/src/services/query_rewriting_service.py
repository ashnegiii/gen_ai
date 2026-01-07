import os
import re
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


class QueryRewritingService:
    """
    Service for query rewriting/optimization to improve retrieval quality in a RAG pipeline.
    
    Main purpose: Transform user queries into a format that retrieves the best FAQ matches.
    
    Techniques implemented:
    1. Query cleaning and normalization
    2. Keyword extraction for hybrid search  
    3. Question reformulation (turning statements into questions)
    4. Multi-query generation for better recall
    5. Conversational context resolution (standalone query from chat history)
    """

    def __init__(self):
        """Initialize the QueryRewritingService."""
        # Stopwords to remove for keyword extraction
        self.stopwords = {
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
            "you", "your", "yours", "yourself", "yourselves", "he", "him",
            "his", "himself", "she", "her", "hers", "herself", "it", "its",
            "itself", "they", "them", "their", "theirs", "themselves",
            "am", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "having", "do", "does", "did", "doing",
            "a", "an", "the", "and", "but", "if", "or", "because", "as",
            "until", "while", "of", "at", "by", "for", "with", "about",
            "against", "between", "into", "through", "during", "before",
            "after", "above", "below", "to", "from", "up", "down", "in",
            "out", "on", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "all",
            "each", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "s", "t", "can", "will", "just", "don", "should", "now", "please",
            "thanks", "thank", "hi", "hello", "hey", "need", "want", "would",
            "could", "help", "know", "get", "got",
            # Question words (not useful as keywords)
            "how", "what", "why", "who", "which", "whom",
            # Negative words (we handle these separately)
            "cant", "cannot", "wont", "doesnt", "dont", "isnt", "arent", "wasnt", "werent",
            # Common verbs that don't add meaning for search
            "offer", "provide", "give", "take", "make", "use", "work", "find", "see", "look",
            "tell", "ask", "try", "call", "keep", "let", "put", "seem", "leave", "feel",
            "accept", "allow", "include", "support"
        }
        
        # Question words that indicate intent
        self.question_starters = ["how", "what", "why", "where", "when", "who", "which", "can", "could", "is", "are", "do", "does"]
        
        # Words that indicate the query references previous context
        self.context_dependent_words = {
            "it", "this", "that", "these", "those", "they", "them",
            "there", "here", "such", "same", "other", "another",
            "also", "too", "either", "neither", "both", "else"
        }

    def rewrite_query(self, query: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, any]:
        """
        Main method to rewrite/optimize a query for better retrieval.
        
        Args:
            query: The original user query
            chat_history: Optional list of previous messages [{"role": "user"|"assistant", "content": "..."}]
            
        Returns:
            Dictionary containing:
            - original_query: The original input
            - cleaned_query: Normalized version (best for embedding search)
            - optimized_query: Best query for retrieval
            - keywords: Extracted keywords for potential keyword/hybrid search
            - query_type: Detected type (question, statement, keyword)
            - is_contextual: Whether the query needed context resolution
        """
        # Step 0: Resolve conversational context if needed
        is_contextual = False
        resolved_query = query
        
        if chat_history and self._needs_context_resolution(query):
            resolved_query = self._resolve_context(query, chat_history)
            is_contextual = True
        
        # Step 1: Clean and normalize
        cleaned = self._clean_query(resolved_query)
        
        # Step 2: Detect query type
        query_type = self._detect_query_type(cleaned)
        
        # Step 3: Extract keywords
        keywords = self._extract_keywords(cleaned)
        
        # Step 4: Reformulate if needed (turn statement into question-like format)
        reformulated = self._reformulate_for_faq(cleaned, query_type)
        
        return {
            "original_query": query,
            "resolved_query": resolved_query,
            "cleaned_query": cleaned,
            "optimized_query": reformulated,
            "keywords": keywords,
            "query_type": query_type,
            "is_contextual": is_contextual
        }

    def _needs_context_resolution(self, query: str) -> bool:
        """
        Check if the query contains words that reference previous context.
        """
        query_lower = query.lower()
        words = set(re.findall(r'\b\w+\b', query_lower))
        
        # Check for context-dependent words (it, this, that, etc.)
        if words & self.context_dependent_words:
            return True
        
        # Check for follow-up patterns (regardless of query length)
        if query_lower.startswith(("what about ", "how about ", "and ", "but ")):
            return True
        
        # Check for implicit context questions (words that imply "in/for what?")
        implicit_context_words = {"included", "available", "supported", "possible", "allowed", "required"}
        if words & implicit_context_words:
            return True
        
        # Check for very short queries that might be follow-ups
        if len(words) <= 3:
            if "?" in query:
                return True
        
        return False

    def _resolve_context(self, query: str, chat_history: List[Dict]) -> str:
        """
        Resolve contextual references using chat history.
        
        This is a heuristic-based approach. For better results, use an LLM.
        """
        if not chat_history:
            return query
        
        # Collect all user messages to find the main topic
        user_messages = [msg.get("content", "") for msg in chat_history if msg.get("role") == "user"]
        
        if not user_messages:
            return query
        
        # Find the most recent STANDALONE question (not a follow-up) to use as topic
        # Work backwards through user messages
        topic_keywords = []
        for user_msg in reversed(user_messages):
            # Check if this message looks like a standalone question
            if not self._needs_context_resolution(user_msg):
                # This is a standalone question - use it as the topic
                topic_keywords = self._extract_keywords(user_msg)
                if topic_keywords:
                    break
        
        # If no standalone question found, use the first message as fallback
        if not topic_keywords:
            topic_keywords = self._extract_keywords(user_messages[0])
        
        if not topic_keywords:
            return query
        
        topic = " ".join(topic_keywords[:2])
        
        query_lower = query.lower().strip()
        
        # Handle common follow-up patterns
        # "What about X?" -> "What is X regarding [topic]?"
        if query_lower.startswith("what about"):
            rest = query[10:].strip().rstrip("?")
            return f"What is {rest} regarding {topic}?"
        
        # "And X?" or "And the X?" -> "What is [topic] X?"
        if query_lower.startswith("and "):
            rest = query[4:].strip().rstrip("?")
            # Remove "the" if present
            if rest.lower().startswith("the "):
                rest = rest[4:]
            return f"What is the {rest} for {topic}?"
        
        # "How about X?" -> "What is X for [topic]?"
        if query_lower.startswith("how about"):
            rest = query[9:].strip().rstrip("?")
            return f"What is {rest} for {topic}?"
        
        # Replace pronouns with topic
        resolved = query
        pronoun_replacements = {
            r'\bit\b': topic,
            r'\bthis\b': topic,
            r'\bthat\b': topic,
            r'\bthey\b': topic,
            r'\bthem\b': topic,
        }
        
        for pattern, replacement in pronoun_replacements.items():
            resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
        
        # If query is very short, prepend topic context
        words = query.split()
        if len(words) <= 4 and resolved == query:
            # Query wasn't modified by pronoun replacement
            # Prepend topic: "doesn't work" -> "password reset doesn't work"
            resolved = f"{topic} {query}"
        
        return resolved

    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize the query.
        """
        if not query:
            return ""
        
        # Convert to lowercase and strip
        cleaned = query.lower().strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove special characters but keep basic punctuation and question marks
        cleaned = re.sub(r'[^\w\s\-\?\!\.\,\']', '', cleaned)
        
        return cleaned

    def _detect_query_type(self, query: str) -> str:
        """
        Detect the type of query to handle it appropriately.
        
        Returns: 'question', 'statement', or 'keyword'
        """
        if not query:
            return "keyword"
        
        words = query.split()
        
        # Check if it starts with a question word
        if words and words[0] in self.question_starters:
            return "question"
        
        # Check if it ends with a question mark
        if query.rstrip().endswith("?"):
            return "question"
        
        # Check if it's just keywords (very short, no verbs)
        if len(words) <= 3:
            return "keyword"
        
        return "statement"

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from the query.
        These can be used for hybrid search or fallback matching.
        """
        if not query:
            return []
        
        # Tokenize
        words = query.lower().split()
        
        # Remove stopwords, short words, and punctuation
        keywords = []
        for word in words:
            # Clean punctuation from word
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word not in self.stopwords and len(clean_word) > 2:
                keywords.append(clean_word)
        
        return keywords

    def _reformulate_for_faq(self, query: str, query_type: str) -> str:
        """
        Reformulate the query to better match FAQ-style questions.
        
        FAQs are typically stored as questions like "How do I...?", "What is...?"
        So we want to format user input similarly for better embedding matches.
        """
        if not query:
            return ""
        
        # If already a question, just clean it up
        if query_type == "question":
            # Ensure it ends with question mark for consistency
            if not query.endswith("?"):
                return query + "?"
            return query
        
        # If keywords only, try to form a question
        if query_type == "keyword":
            keywords = self._extract_keywords(query)
            if keywords:
                # Form a simple "how to" question from keywords
                return f"how do i {' '.join(keywords)}?"
            return query
        
        # For statements, try to convert to question form
        # e.g., "I can't reset my password" -> "how do i reset my password?"
        # e.g., "password reset not working" -> "how do i reset password?"
        
        keywords = self._extract_keywords(query)
        if keywords:
            # Check for problem indicators
            problem_words = {"not", "can't", "cant", "cannot", "won't", "wont", "doesn't", "doesnt", "isn't", "isnt", "problem", "issue", "error", "help"}
            has_problem = any(word in query.lower() for word in problem_words)
            
            if has_problem:
                return f"how do i {' '.join(keywords)}?"
            else:
                return f"what is {' '.join(keywords)}?"
        
        return query

    def get_optimized_query(self, query: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        Simple method that returns the best single query for retrieval.
        
        Use this when you just need one optimized query string for embedding search.
        
        Args:
            query: The user's query
            chat_history: Optional chat history for context resolution
        """
        result = self.rewrite_query(query, chat_history)
        return result["optimized_query"]

    def get_multi_queries(self, query: str, chat_history: Optional[List[Dict]] = None) -> List[str]:
        """
        Generate multiple query variations for better retrieval recall.
        
        Returns a list of queries to search with. Search with all and combine/dedupe results.
        This improves recall by matching different phrasings of the same question.
        
        Args:
            query: The user's query
            chat_history: Optional chat history for context resolution
        """
        result = self.rewrite_query(query, chat_history)
        
        queries = []
        
        # 1. Optimized/reformulated query (best for FAQ matching)
        queries.append(result["optimized_query"])
        
        # 2. Cleaned original (preserves user's exact phrasing)
        if result["cleaned_query"] != result["optimized_query"]:
            queries.append(result["cleaned_query"])
        
        # 3. Keywords only (for sparse/keyword matching if available)
        if result["keywords"] and len(result["keywords"]) >= 2:
            keyword_query = " ".join(result["keywords"])
            if keyword_query not in queries:
                queries.append(keyword_query)
        
        return queries
