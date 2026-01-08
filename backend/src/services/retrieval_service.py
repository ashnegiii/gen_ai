# TODO Paula: Implement methods for retrieval
"""
TAKEN FROM 1
The code for creating vector embeddings for the query using the SentenceTransformers library was taken from https://sbert.net/docs/quickstart.html

TAKEN FROM 2
The code for retrieving the top k similar results from the vector database was based on the following tutorial: https://www.tigerdata.com/learn/using-pgvector-with-python

TAKEN FROM 3
The way in which the SQL query for retrieving the top k similar results from the DB was written was based on the following sources:

https://github.com/pgvector/pgvector?tab=readme-ov-file#getting-started
https://stackoverflow.com/a/43226395
"""

from typing import List
from sentence_transformers import SentenceTransformer
from services.indexing_service import IndexingService

class RetrievalService:
    def retrieve_documents(self, optimized_query: str, indexing_service: IndexingService) -> List[str]:

        """
        Retrieve relevant documents
        input -> optimized_query (optimized query from the first RAG step) & indexing_service (from pipeline.py)
        output -> List[(str, str)]: list containing the top-k tuples with the format (relevant chunk, corresponding metadata)
        """

        indexing_service._ensure_connection()
        embedding_model_name = indexing_service.model_name
        conn = indexing_service.conn

        top_k_results = []

        # TAKEN FROM START 1
        model = SentenceTransformer(embedding_model_name)
        query_embedding = model.encode(optimized_query).tolist()
        # TAKEN FROM END 1

        # retrieve from DB and return top k

        # TAKEN FROM START 2
        cur = conn.cursor()
        # TAKEN FROM START 3
        retrieve_command = f"SELECT question_embedding, answer_embedding \n FROM faqs \n ORDER BY answer_embedding <=> '{query_embedding}' LIMIT 5;"
        # TAKEN FROM END 3
        cur.execute(retrieve_command)
        similar_results = cur.fetchall()
        indexing_service.close()
        # TAKEN FROM END 2

        # at the moment, similar_results is not used for top_k_results, but should be
        return top_k_results
