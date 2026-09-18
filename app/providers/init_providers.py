import os
from pathlib import Path

from app.providers.postgres_db_provider import PostgresDBProvider
from app.providers.ollama_llm_provider import OllamaLLMProvider
# from app.providers.selectel_llm_provider import SelectelLLMProvider
from app.bot import Bot

DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE = PostgresDBProvider(DATABASE_URL)


OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3.6:27b"
OLLAMA_TIMEOUT=120


SELECTEL_URL="https://api.selectel.ru/aig/v1"
SELECTEL_API_KEY=os.environ["SELECTEL_API_KEY"]
SELECTEL_MODEL="qwen/qwen3.6-27b"


# список документов .md в папке resources
BOT_DOC_PATH_LIST = sorted(
    path
    for path in Path("app/resources").glob("*.md")
    if path.is_file()
)


LLM_PROVIDER = OllamaLLMProvider(OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT)
# LLM_PROVIDER = SelectelLLMProvider(SELECTEL_URL, SELECTEL_API_KEY, SELECTEL_MODEL)
BOT = Bot(LLM_PROVIDER, DATABASE, BOT_DOC_PATH_LIST)
