from backend.src.services.generation_service import GenerationService
from backend.src.services.indexing_service import IndexingService
from backend.src.services.query_rewriting_service import QueryRewritingService
from backend.src.services.retrieval_service import RetrievalService


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

    def index_document(self):
        # Kevin: Index the uploaded document

        pass

    def query(self):
        # Step 1 (Kevin): Optimize the user's query for better retrieval

        # Step 2 (Paula): Search for relevant chunks using the optimized query

        # Step 3 (Moritz): Generate a response using the retrieved chunks and the original query

        pass
