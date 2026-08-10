from typing import Any
from ollama import AsyncClient
from uuid import uuid4

from app.schemas import Message, Role, Tool


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

    # метод, работающий с tools

    async def generate_completion_with_tools_async(
        self,
        messages: list[Message],
        tools: dict[str, Any]
    ) -> Tool | Message:
        response = await self.async_client.chat(
            model=self.ollama_model,
            messages=messages,
            # передаем список инструментов
            tools=list(tools.values()),
            think=True
        )

        print("LLM_PROVIDER_RESPONSE", response)
        
        message_from_llm: list[Tool] = []
        
        if (response.message.tool_calls):
            for call in response.message.tool_calls:
                tool_name = call.function.name
                arguments = call.function.arguments

                message_from_llm.append(Tool(
                    tool_name,
                    arguments
                ))

        print("MESSAGE_FROM_LLM", message_from_llm)

        return message_from_llm
