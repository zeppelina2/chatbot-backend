from openai import AsyncOpenAI
from typing import Any
import yaml
import inspect
import json
from collections.abc import Callable
from typing import Any, get_type_hints
from openai.types.chat import ChatCompletionToolParam
from pydantic import ConfigDict, create_model

from app.schemas import Message, Role, Tool

class SelectelLLMProvider:
    """
    Провайдер для работы с Selectel LLM.

    Обеспечивает асинхронные методы для генерации ответов
    через сервера Selectel
    """
    
    def __init__(self, selectel_url: str, selectel_api_key: str, selectel_model: str):
        self.selectel_url = selectel_url
        self.selectel_api_key = selectel_api_key
        self.selectel_model = selectel_model

        with open("app/prompts.yaml") as file:
            self.prompts = yaml.safe_load(file)["prompts"]

        # Асинхронный клиент
        self.async_client = AsyncOpenAI(
            base_url=selectel_url,
            api_key=selectel_api_key
        )


    def create_tool_schemas(
        self,
        tools: dict[str, Callable[..., Any]],
    ) -> list[ChatCompletionToolParam]:
        """Создать схемы инструментов из функций или привязанных методов."""
        schemas: list[ChatCompletionToolParam] = []

        for tool_name, tool in tools.items():
            signature = inspect.signature(tool)
            type_hints = get_type_hints(tool, include_extras=True)

            fields: dict[str, Any] = {}

            for name, parameter in signature.parameters.items():
                # Инструменты вызываются через tool(**arguments).
                # ... обозначает обязательное поле в Pydantic.
                default = (
                    ...
                    if parameter.default is inspect.Parameter.empty
                    else parameter.default
                )

                fields[name] = (type_hints[name], default)

            parameters_model = create_model(
                f"{tool_name}_parameters",
                __config__=ConfigDict(extra="forbid"),
                **fields,
            )

            parameters_schema = parameters_model.model_json_schema()

            # Название внутренней модели не нужно в описании параметров.
            parameters_schema.pop("title", None)

            schemas.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": inspect.getdoc(tool) or "",
                    "parameters": parameters_schema,
                },
            })

        return schemas


    # метод, работающий с tools
    async def generate_completion_with_tools_async(
        self,
        messages: list[Message],
        tools: dict[str, Callable[..., Any]],
    ) -> Tool | Message:
        # опишем tool схему
        tool_options: dict[str, Any] = {
            "tools": self.create_tool_schemas(tools),
            "tool_choice": "auto",
            "parallel_tool_calls": False,
        }

        response = await self.async_client.chat.completions.create(
            model=self.selectel_model,
            messages=messages,
            stream=False,
            **tool_options,
        )
        
        response_message = response.choices[0].message

        # обрабатываем ответ с tools, берем только один tool,
        # не будем позволять работать с несколькими тулами одновременно,
        # пусть модель обращается к тулам последовательно
        if (response_message.tool_calls):
            call = response_message.tool_calls[0]
            tool_name = call.function.name
            arguments = json.loads(call.function.arguments)

            return Tool(
                tool_name=tool_name,
                arguments=arguments,
                tool_call_id=call.id,
            )
        else:
            # обрабатываем ответ с message
            return Message(content=response_message.content, role=Role.ASSISTANT)


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

        response = await self.async_client.chat.completions.create(
            model=self.selectel_model,
            messages=message_for_llm,
            stream=False,
        )

        return response.choices[0].message.content

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
