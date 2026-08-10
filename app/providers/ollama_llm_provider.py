from typing import Any
from ollama import AsyncClient
from uuid import uuid4

from app.schemas import MessageListSchema, MessageSchema, Role


class OllamaLLMProvider:
    """
    Провайдер для работы с Ollama LLM.

    Обеспечивает асинхронные методы для генерации ответов
    через локально запущенный Ollama сервер
    """

    def __init__(self, ollama_url, ollama_model, ollama_timeout):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.ollama_timeout = ollama_timeout

        # Асинхронный клиент
        self.async_client = AsyncClient(
            host=ollama_url,
            timeout=ollama_timeout
        )

    async def generate_completion_async(
        self,
        messages: MessageListSchema
    ) -> MessageSchema:

        format_messages = MessageListSchema.to_raw_messages(messages)

        try:
            response = await self.async_client.chat(
                model=self.ollama_model,
                messages=format_messages
            )

            message_from_llm = MessageSchema(
                message_id=str(uuid4()),
                content=response.message.content,
                created_at=response.created_at,
                updated_at=response.created_at,
                role=Role.ASSISTANT
            )

            return message_from_llm

        except Exception as e:
            raise Exception(f"Ошибка при запросе к Ollama: {str(e)}") from e

    # метод, работающий с tools
    async def generate_completion_with_tools_async(
        self,
        messages: MessageListSchema,
        tools: dict[str, Any]
    ) -> MessageSchema:
        response = await self.async_client.chat(
            model=self.ollama_model,
            messages=messages,
            # передаем список инструментов
            tools=list(tools.values()),
            think=True
        )
        
        return response
