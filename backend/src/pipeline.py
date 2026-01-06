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

    def query(self, query):
        # Step 1 (Kevin): Optimize the user's query for better retrieval

        # Step 2 (Paula): Search for relevant chunks using the optimized query
        self.retrieval_service.retrieve_documents(query, self.indexing_service)
        # Step 3 (Moritz): Generate a response using the retrieved chunks and the original query

        pass