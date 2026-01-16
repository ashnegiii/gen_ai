from services.generation_service import GenerationService
from services.indexing_service import IndexingService
from services.query_rewriting_service import QueryRewritingService
from services.retrieval_service import RetrievalService


class RAGPipeline:
    """
    Orchestrates the complete RAG pipeline
    """

    def __init__(self):
        """Initialize all services"""
        self.indexing_service = IndexingService()
        self.query_rewriting_service = QueryRewritingService()
        self.retrieval_service = RetrievalService()
        self.generation_service = GenerationService()

    def index_document(self, documents):
        """Index documents into the vector database."""
        return self.indexing_service.index_documents(documents)

    def run_rag_pipeline(self, user_query, document_id, chat_history):
        # Step 1 (Kevin): Query Rewriting
        rewriting_result = self.query_rewriting_service.rewrite_query(user_query, chat_history)
        optimized_query = rewriting_result.get("cleaned_query", user_query)

        print(f"DEBUG: Original: '{user_query}' -> Optimized: '{optimized_query}'")
        
        # Step 2 (Paula): Retrieval
        chunks = self.retrieval_service.retrieve_documents(
            optimized_query,
            document_id,
            self.indexing_service
        )
        # Step : Generation
        return self.generation_service.generate_response_stream(query=user_query, retrieved_chunks=chunks)