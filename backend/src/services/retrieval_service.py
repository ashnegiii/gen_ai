"""
TAKEN FROM 1
The code for creating vector embeddings for the query using the SentenceTransformers library was taken from https://sbert.net/docs/quickstart.html

TAKEN FROM 2
The code for retrieving the top k similar results from the vector database was based on the following tutorial: https://www.tigerdata.com/learn/using-pgvector-with-python

TAKEN FROM 3
The way in which the SQL query for retrieving the top k similar results from the DB was written was based on the following sources:

https://github.com/pgvector/pgvector?tab=readme-ov-file#getting-started
https://stackoverflow.com/a/43226395
https://docs.cloud.google.com/alloydb/docs/ai/run-vector-similarity-search#run-pgvector-similarity-search
"""

from typing import List
from sentence_transformers import SentenceTransformer
from .indexing_service import IndexingService

class RetrievalService:
    def retrieve_documents(self, optimized_query: str, document_id: str, indexing_service: IndexingService) -> List[str]:

        """
        Retrieve relevant documents by comparing the embeddings of the user's query and the answers found in the knowledge base
        """

        indexing_service._ensure_connection()
        embedding_model_name = indexing_service.model_name
        conn = indexing_service.conn

        k = 5 # the top k relevant/similar results will be retrieved from the knowledge base

        # TAKEN FROM START 1
        model = SentenceTransformer(embedding_model_name)
        query_embedding = model.encode(
            optimized_query,
            show_progress_bar=False
        ).tolist()
        # TAKEN FROM END 1

        # TAKEN FROM START 2
        cur = conn.cursor()
        # TAKEN FROM START 3
        # the cosine distance, namely <=>, is used
        retrieve_query = f"SELECT answer_text \n FROM faqs WHERE document_id={document_id} \n ORDER BY answer_embedding::vector <=> '{query_embedding}' LIMIT {k};"
        # TAKEN FROM END 3
        cur.execute(retrieve_query)
        raw_results = cur.fetchall()
        # Unpack the results to extract the string from the tuples
        relevant_results = [row[0] for row in raw_results]
        indexing_service.close()
        # TAKEN FROM END 2
        return relevant_results