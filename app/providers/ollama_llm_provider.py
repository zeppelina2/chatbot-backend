from typing import Any
from ollama import AsyncClient
import yaml
from uuid import uuid4
import json

from app.schemas import Message, Role, Tool


class OllamaLLMProvider:
    """
    Провайдер для работы с Ollama LLM.

    Обеспечивает асинхронные методы для генерации ответов
    через локально запущенный Ollama сервер
    """

    def __init__(self, ollama_url: str, ollama_model: str, ollama_timeout: int):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.ollama_timeout = ollama_timeout
        with open("app/prompts.yaml") as file:
            self.prompts = yaml.safe_load(file)["prompts"]

        # Асинхронный клиент
        self.async_client = AsyncClient(
            host=ollama_url,
            timeout=ollama_timeout
        )


    def prepare_messages_for_ollama(
        self,
        messages: list[Message],
    ) -> list[dict[str, Any]]:
        prepared_messages: list[dict[str, Any]] = []

        # Связываем сохранённый ID вызова с именем инструмента.
        tool_names_by_id: dict[str, str] = {}

        for message in messages:
            prepared: dict[str, Any] = {
                "role": message.role,
                "content": message.content or "",
            }

            if message.tool_calls:
                ollama_tool_calls = []

                for call in message.tool_calls:
                    function = call["function"]
                    arguments = function["arguments"]

                    # Поддерживаем и новый формат, и старые словари.
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)

                    call_id = call.get("id")

                    if call_id:
                        tool_names_by_id[call_id] = function["name"]

                    ollama_tool_calls.append({
                        "function": {
                            "name": function["name"],
                            "arguments": arguments,
                        },
                    })

                prepared["tool_calls"] = ollama_tool_calls

            if message.role == Role.TOOL:
                tool_name = tool_names_by_id.get(message.tool_call_id)

                if tool_name:
                    prepared["tool_name"] = tool_name

            prepared_messages.append(prepared)

        return prepared_messages


    # метод, работающий с tools
    async def generate_completion_with_tools_async(
        self,
        messages: list[Message],
        tools: dict[str, Any]
    ) -> Tool | Message:
        response = await self.async_client.chat(
            model=self.ollama_model,
            messages=self.prepare_messages_for_ollama(messages),
            # передаем список инструментов
            tools=list(tools.values()),
            think=False
        )

        # обрабатываем ответ с tools, берем только один tool,
        # не будем позволять работать с несколькими тулами одновременно,
        # пусть модель обращается к тулам последовательно
        if (response.message.tool_calls):
            call = response.message.tool_calls[0]
            tool_name = call.function.name
            arguments = call.function.arguments

            return Tool(
                tool_name=tool_name,
                arguments=arguments,
                tool_call_id=f"call_{uuid4().hex}",
            )
        else:
            # обрабатываем ответ с message
            return Message(content=response.message.content, role=Role.ASSISTANT)


    # функция берет json и делает из него строку
    @staticmethod # это значит, что self не нужен
    def tool_to_str(tool: Tool) -> str:
        return tool.model_dump_json(indent=2, ensure_ascii=False)


    # метод, генерирующий имя для диалога
    async def generate_dialogue_name_async(
        self,
        message: str,
    ) -> str:
        # контекст для модели
        message_for_llm = [
            Message(
                role=Role.SYSTEM,
                content=self.prompts["system_promt_generate_dialogue_name"],
            ),
            Message(
                role=Role.USER,
                content=message,
            ),
        ]

        response = await self.async_client.chat(
            model=self.ollama_model,
            messages=message_for_llm,
            think=False
        )


        return response.message.content


    def tool_to_assistant_message(self, tool: Tool) -> Message:
        return Message(
            role=Role.ASSISTANT,
            content="",
            tool_calls=[
                {
                    "id": tool.tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool.tool_name,
                        "arguments": json.dumps(
                            tool.arguments,
                            ensure_ascii=False,
                        ),
                    },
                },
            ],
        )
