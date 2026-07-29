import os

from app.postgres_db_provider import PostgresDBProvider
from app.ollama_llm_provider import OllamaLLMProvider

DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE = PostgresDBProvider(DATABASE_URL)


OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3.6:27b"
OLLAMA_TIMEOUT=120
LLM_PROVIDER = OllamaLLMProvider(OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT)
