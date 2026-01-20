import logging
from services.generation_service import GenerationService
from services.indexing_service import IndexingService
from services.query_rewriting_service import QueryRewritingService
from services.retrieval_service import RetrievalService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        file_size = sum(len(doc.get('content', '')) for doc in documents)
        faq_entries = [faq for doc in documents for faq in doc.get('faqs', [])]
        return self.indexing_service.index_documents(documents, file_size=file_size, faq_entries=faq_entries)

    def run_rag_pipeline(self, user_query, document_id, chat_history, k=3):
        # Step 1 (Kevin): Query Rewriting
        rewriting_result = self.query_rewriting_service.rewrite_query(user_query, chat_history)
        optimized_query = rewriting_result.get("cleaned_query", user_query)

        logger.info(f"Original query: '{user_query}' optimized to: '{optimized_query}'")

        # Step 2 (Paula): Retrieval
        chunks = self.retrieval_service.retrieve_documents(
            optimized_query,
            document_id,
            self.indexing_service
        )
        logger.info(f"Retrieved {len(chunks)} chunks for query '{optimized_query}'")

        # Step 3: Generation
        logger.info(f"Starting response generation with {k} chunks.")
        return self.generation_service.generate_response_stream(query=user_query, retrieved_chunks=chunks, k=k)