import os

from app.providers.postgres_db_provider import PostgresDBProvider
from app.providers.ollama_llm_provider import OllamaLLMProvider
from app.tools.bot import Bot

DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE = PostgresDBProvider(DATABASE_URL)


OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3.6:27b"
OLLAMA_TIMEOUT=120
LLM_PROVIDER = OllamaLLMProvider(OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT)
BOT = Bot(LLM_PROVIDER, DATABASE)
