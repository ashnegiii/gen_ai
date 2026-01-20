import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "gen_ai")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

config = Config()