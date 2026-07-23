from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import uvicorn

load_dotenv()

from app.init_providers import DATABASE
from app.routers import dialogues, messages, llm

# создаем базу или берем существующую, запустится при старте
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await DATABASE.init_db()
    yield

# инициализация fastapi
app = FastAPI(
    title="Python Chatbot Project API",
    description="REST API для pet-проекта на React",
    version="0.1.0",
    lifespan=lifespan
)

# Настройка CORS для React фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # порт Vite/Create React App
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(dialogues.router, prefix="/api", tags=["dialogues"])
app.include_router(messages.router, prefix="/api", tags=["messages"])
app.include_router(llm.router, prefix="/api", tags=["llm"])

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}

# запуск fastapi
if __name__ == "__main__":
    uvicorn.run(app)
