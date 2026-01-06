import os
from typing import Dict, List, Optional

import numpy as np
import psycopg
from dotenv import load_dotenv

load_dotenv()


class IndexingService:
    """Service for indexing FAQ documents into the vector database."""

    def __init__(self, db_config: Optional[Dict] = None):
        """Initialize the IndexingService with database configuration."""
        if db_config is None:
            db_config = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": os.getenv("POSTGRES_PORT", "5433"),
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
        
        # Documents table - tracks uploaded files
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
              id SERIAL PRIMARY KEY,
              name TEXT NOT NULL,
              size_bytes INTEGER NOT NULL DEFAULT 0,
              created_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        
        # FAQs table - with foreign key to documents
        cur.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
              id SERIAL PRIMARY KEY,
              document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
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
        cur.execute("""
            CREATE INDEX IF NOT EXISTS faqs_document_id_idx 
            ON faqs (document_id);
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

    def index_documents(self, filename: str, file_size: int, faq_entries: List[Dict]) -> Dict[str, any]:
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

        if not faq_entries: 
            return {"status": "success", "indexed_count": 0, "message": "Keine FAQs zum Indizieren"}

        # Flatten all FAQs from all documents
        try:
            cur = self.conn.cursor()
            
            # 1. create document entry
            cur.execute("""
                INSERT INTO documents (name, size_bytes)
                VALUES (%s, %s)
                RETURNING id
            """, (filename, file_size))
            document_id = cur.fetchone()[0]

            # 2. compute embeddings    
            q_texts = [f["question"] for f in faq_entries]
            a_texts = [f["answer"] for f in faq_entries]

            q_embs = self._texts_to_embeddings(q_texts)
            a_embs = self._texts_to_embeddings(a_texts)

            # 3. insert FAQs with document_id
            insert_data = [
                (document_id, faq["question"], faq["answer"], q_emb.tolist(), a_emb.tolist())
                for faq, q_emb, a_emb in zip(faq_entries, q_embs, a_embs)
            ]
            
            cur.executemany("""
                INSERT INTO faqs (document_id, question_text, answer_text, question_embedding, answer_embedding)
                VALUES (%s, %s, %s, %s, %s)
            """, insert_data)

            self.conn.commit()

            return {
                "status": "success",
                "indexed_count": len(faq_entries),
                "document_id": document_id,
                "message": f"Erfolgreich {len(faq_entries)} FAQs aus '{filename}' indiziert"
            }
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise e

    def get_stats(self) -> Dict[str, any]:
        """Get database statistics."""
        self._ensure_connection()
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM faqs")
        total = cur.fetchone()[0]
        return {"total_faqs": total}

    def get_all_documents(self) -> List[Dict]:
        """
        Get all uploaded documents (files) from the database.
        
        Returns:
            List of documents with id, name, uploadedAt, and size
        """
        self._ensure_connection()
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, name, size_bytes, created_at 
            FROM documents 
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        
        documents = []
        for row in rows:
            doc_id, name, size_bytes, created_at = row
            # Format size
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            else:
                size_str = f"{size_bytes / 1024:.1f} KB"
            
            documents.append({
                "id": str(doc_id),
                "name": name,
                "uploadedAt": created_at.isoformat() if created_at else "",
                "size": size_str
            })
        
        return documents

    def delete_document(self, doc_id: str) -> Dict[str, any]:
        """
        Delete a document and all its associated FAQs by document ID.
        
        Args:
            doc_id: The ID of the document to delete
            
        Returns:
            Dict with status and message
        """
        self._ensure_connection()
        cur = self.conn.cursor()
        
        # Check if document exists
        cur.execute("SELECT id, name FROM documents WHERE id = %s", (int(doc_id),))
        doc = cur.fetchone()
        if doc is None:
            return {
                "status": "error",
                "message": f"Document with id {doc_id} not found"
            }
        
        doc_name = doc[1]
        
        # Count FAQs that will be deleted
        cur.execute("SELECT COUNT(*) FROM faqs WHERE document_id = %s", (int(doc_id),))
        faq_count = cur.fetchone()[0]
        
        # Delete the document (FAQs will be cascade deleted)
        cur.execute("DELETE FROM documents WHERE id = %s", (int(doc_id),))
        self.conn.commit()
        
        return {
            "status": "success",
            "message": f"Document '{doc_name}' with {faq_count} FAQ(s) deleted successfully",
            "id": doc_id
        }

    def clear_all_documents(self) -> Dict[str, any]:
        """
        Delete all documents and FAQs from the database.
        
        Returns:
            Dict with status and count of deleted documents
        """
        self._ensure_connection()
        cur = self.conn.cursor()
        
        # Get counts before deletion
        cur.execute("SELECT COUNT(*) FROM documents")
        doc_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM faqs")
        faq_count = cur.fetchone()[0]
        
        # Delete all (FAQs will cascade)
        cur.execute("DELETE FROM documents")
        # Also delete any orphaned FAQs (from old schema)
        cur.execute("DELETE FROM faqs")
        self.conn.commit()
        
        return {
            "status": "success",
            "message": f"Deleted {doc_count} document(s) with {faq_count} FAQ(s) from database",
            "deleted_documents": doc_count,
            "deleted_faqs": faq_count
        }

    def index_from_csv(self, csv_content: str, filename: str = "uploaded.csv") -> Dict[str, any]:
        """
        Index FAQs from CSV content, creating a document entry to group them.
        
        Expected CSV format:
        question,answer
        "How do I...?","You can..."
        
        Args:
            csv_content: CSV string with question,answer columns
            filename: Name of the uploaded file
            
        Returns:
            Dict with status and count of indexed FAQs
        """
        import csv
        import io
        
        self._ensure_connection()
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        all_faqs = []
        for row in reader:
            all_faqs.append({
                "question_text": row["question"],
                "answer_text": row["answer"]
            })
        
        if not all_faqs:
            return {"status": "success", "indexed_count": 0, "message": "No FAQs to index"}
        
        # Calculate file size
        size_bytes = len(csv_content.encode('utf-8'))
        
        # Create document entry
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO documents (name, size_bytes)
            VALUES (%s, %s)
            RETURNING id
        """, (filename, size_bytes))
        document_id = cur.fetchone()[0]
        
        # Compute embeddings
        q_texts = [f["question_text"] for f in all_faqs]
        a_texts = [f["answer_text"] for f in all_faqs]
        
        q_embs = self._texts_to_embeddings(q_texts)
        a_embs = self._texts_to_embeddings(a_texts)
        
        # Insert FAQs with document_id using executemany for better performance
        insert_data = [
            (document_id, faq["question_text"], faq["answer_text"], q_emb.tolist(), a_emb.tolist())
            for faq, q_emb, a_emb in zip(all_faqs, q_embs, a_embs)
        ]
        cur.executemany("""
            INSERT INTO faqs (document_id, question_text, answer_text, question_embedding, answer_embedding)
            VALUES (%s, %s, %s, %s, %s)
        """, insert_data)
        
        self.conn.commit()
        
        return {
            "status": "success",
            "indexed_count": len(all_faqs),
            "document_id": document_id,
            "message": f"Successfully indexed {len(all_faqs)} FAQs from '{filename}'"
        }

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