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

        if (response.message.tool_calls):
            call = response.message.tool_calls[0]
            tool_name = call.function.name
            arguments = call.function.arguments

            return Tool(tool_name=tool_name, arguments=arguments)
        else:
            return Message(content=response.message.content, role=Role.ASSISTANT) 

    @staticmethod # это значит, что self не нужен
    def tool_to_str(tool: Tool) -> str:
        return tool.model_dump_json(indent=2, ensure_ascii=False)
