"""
Fetch and return FAQs for a given document from the database
"""
import os
from dotenv import load_dotenv
import psycopg
from typing import List, Dict, Optional

load_dotenv()


def _get_db_config() -> Dict[str, str]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5433"),
        "database": os.getenv("POSTGRES_DB", "gen_ai"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }


def _connect() -> psycopg.Connection:
    d = _get_db_config()
    conn_str = (
        f"host={d['host']} port={d['port']} dbname={d['database']} "
        f"user={d['user']} password={d['password']}"
    )
    return psycopg.connect(conn_str, connect_timeout=5)


def fetch_faqs(
    document_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, str]]:
    """
    Docstring

    :param document_id: The ID of the document that the FAQ should be taken from
    :type document_id: int
    :param base_url: The API that is used to prompt our model
    :type base_url: str
    :param limit: The number of FAQs that should be retrieved
    :type limit: int
    """

    sql_select = """
        SELECT id, document_id, question_text, answer_text
        FROM faqs
    """
    params = []
    if document_id is not None:
        sql_select += " WHERE document_id = %s"
        params.append(int(document_id))

    sql_select += " ORDER BY id"

    if limit is not None:
        sql_select += " LIMIT %s"
        params.append(int(limit))

    if offset:
        sql_select += " OFFSET %s"
        params.append(int(offset))

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_select, params)
            rows = cur.fetchall()

    return [
        {"faq_id": str(r[0]), "document_id": r[1],
         "question": r[2], "reference_answer": r[3]}
        for r in rows
    ]
