import os
import numpy as np
import psycopg
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class IndexingService:
    """Service for indexing FAQ documents into the vector database."""

    def __init__(self, db_config: Optional[Dict] = None):
        """Initialize the IndexingService with database configuration."""
        if db_config is None:
            db_config = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": os.getenv("POSTGRES_PORT", "5432"),
                "database": os.getenv("POSTGRES_DB", "gen_ai"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
            }
        self.db_config = db_config
        self.conn: Optional[psycopg.Connection] = None
        self._ensure_connection()
        self.model_name = "all-MiniLM-L6-v2"

    def _ensure_connection(self):
        """Ensure database connection exists and tables are created."""
        if self.conn is None:
            d = self.db_config
            conn_str = f"host={d['host']} port={d['port']} dbname={d['database']} user={d['user']} password={d['password']}"
            self.conn = psycopg.connect(conn_str, connect_timeout=5)
            self._create_tables()

    def _create_tables(self):
        """Create necessary tables and indexes if they don't exist."""
        cur = self.conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
              id SERIAL PRIMARY KEY,
              question_text TEXT NOT NULL,
              answer_text TEXT NOT NULL,
              question_embedding vector(384) NOT NULL,
              answer_embedding vector(384) NOT NULL,
              created_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS faqs_qemb_idx 
            ON faqs USING ivfflat (question_embedding vector_cosine_ops) 
            WITH (lists = 100);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS faqs_aemb_idx 
            ON faqs USING ivfflat (answer_embedding vector_cosine_ops) 
            WITH (lists = 100);
        """)
        self.conn.commit()

    def _texts_to_embeddings(self, texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
        """Convert texts to embeddings using SentenceTransformer."""
        self.model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            embs = model.encode(
                texts, convert_to_numpy=True).astype(np.float32)
        except Exception as e:
            print(
                f"Warning: Could not load SentenceTransformer model. Using random embeddings. Error: {e}")
            # Fallback: deterministic random vectors
            rng = np.random.RandomState(42)
            dim = 384
            embs = rng.randn(len(texts), dim).astype(np.float32)
            norms = np.linalg.norm(embs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embs = embs / norms
        return embs

    def index_documents(self, documents: List[Dict]) -> Dict[str, any]:
        """
        Index documents with FAQs into the database.

        Expected format:
        [
            {
                "faqs": [
                    {"question": "...", "answer": "..."},
                    {"question": "...", "answer": "..."}
                ]
            }
        ]

        Returns:
            Dict with status and count of indexed FAQs
        """
        self._ensure_connection()

        # Flatten all FAQs from all documents
        all_faqs = []
        for doc in documents:
            for faq in doc.get("faqs", []):
                all_faqs.append({
                    "question_text": faq["question"],
                    "answer_text": faq["answer"]
                })

        if not all_faqs:
            return {"status": "success", "indexed_count": 0, "message": "No FAQs to index"}

        # Compute embeddings
        q_texts = [f["question_text"] for f in all_faqs]
        a_texts = [f["answer_text"] for f in all_faqs]

        q_embs = self._texts_to_embeddings(q_texts)
        a_embs = self._texts_to_embeddings(a_texts)

        # Insert into database
        cur = self.conn.cursor()
        for faq, q_emb, a_emb in zip(all_faqs, q_embs, a_embs):
            cur.execute("""
                INSERT INTO faqs (question_text, answer_text, question_embedding, answer_embedding)
                VALUES (%s, %s, %s, %s)
            """, (faq["question_text"], faq["answer_text"], q_emb.tolist(), a_emb.tolist()))

        self.conn.commit()

        return {
            "status": "success",
            "indexed_count": len(all_faqs),
            "message": f"Successfully indexed {len(all_faqs)} FAQs from {len(documents)} document(s)"
        }

    def get_stats(self) -> Dict[str, any]:
        """Get database statistics."""
        self._ensure_connection()
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM faqs")
        total = cur.fetchone()[0]
        return {"total_faqs": total}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()