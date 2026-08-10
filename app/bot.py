from datetime import datetime
from uuid import UUID, uuid4
from collections.abc import Asyncgenerator

import yaml

from app.tools.search_tool import markdown_search_text
from app.schemas import (
    MessageSchemaBD,
    MessageListSchema,
    Message,
    DeleteMessageListSchema,
    Role,
    DialogueSchema,
    DialogueListSchema
)


class Bot:
    def __init__(self, llm_provider, db_provider):
        self.llm_provider = llm_provider
        self.db_provider = db_provider
        with open("app/prompts.yaml") as file:
            self.prompts = yaml.safe_load(file)["prompts"]

        # список инструментов
        self.tools = {
            "markdown_search_text": markdown_search_text,
        }

    async def process_messages(
        self,
        messages: list[Message],
        # максимальное количество обращений к инструментам
        # (всего, не каждого по отдельности)
        max_steps=5
    ) -> Asyncgenerator[Message]:

        # контекст для модели
        messages_for_llm = [
            Message(role=Role.SYSTEM, content=self.prompts["system_ecumene_prompt"]),
            *messages
        ]

        # счетчик шагов
        step = 0

        try:
            while step < max_steps:
                step += 1

                print("step", step)

                # обращение к LLM
                # на первом шаге на вход передаем сообщения из диалога
                # на последующих шагах передаем сообщения из: диалога, tools,
                # системы
                response = await self.llm_provider.generate_completion_with_tools_async(
                    messages_for_llm,
                    self.tools
                )

                # добавляем ответ ассистента:
                # в контекст
                messages_for_llm.append(response.message)
                yield response.message

                # если инструментов нет, то прерываем цикл
                if not response.message.tool_calls:
                    return

                # в ответ ollama вернет json. если нужно обращение к tool, то в json будет tool_calls.
                # если в сообщении от llm есть tool_calls, то обращаемся к инструментам
                # (их может быть несколько, обработаем их в цикле)
                for call in response.message.tool_calls:
                    tool_name = call.function.name
                    args = call.function.arguments
                    tool_func = self.tools.get(tool_name)

                    # обращаемся к инструменту
                    if not tool_func:
                        result = f"Unknown tool: {tool_name}"
                    else:
                        try:
                            result = tool_func(**args)
                        except Exception as tool_error:
                            result = f"Tool error: {str(tool_error)}"

                    tool_content = str(result)

                    # добавляем ответ инструмента:
                    # в контекст
                    messages_for_llm.append({
                        "role": Role.TOOL,
                        "tool_name": tool_name,
                        "content": tool_content
                    })

            return MessageListSchema(messages=messages_for_base)

        except Exception as e:
            raise Exception(f"Ошибка при запросе к LLM: {str(e)}") from e

    async def get_message_list(self, chat_id: UUID) -> MessageListSchema:
        messages = await self.db_provider.get_message_list(chat_id)
        return messages

    async def create_message(self, chat_id: UUID,
                             message: Message) -> MessageSchemaBD:
        new_message = await self.db_provider.create_message(chat_id, message)
        return new_message

    async def delete_message_list(
            self, chat_id: UUID, message_list: list[UUID]) -> DeleteMessageListSchema:
        response = await self.db_provider.delete_message_list(chat_id, message_list)
        return response

    async def get_dialogue_list(self, user_id: UUID) -> DialogueListSchema:
        dialogues = await self.db_provider.get_dialogue_list(user_id)
        return dialogues

    async def create_dialogue(self, user_id: UUID) -> DialogueSchema:
        new_dialogue = await self.db_provider.create_dialogue(user_id)
        return new_dialogue

    async def change_dialogue_name(
            self, chat_id: UUID, name: str) -> DialogueSchema:
        edit_dialogue = await self.db_provider.change_dialogue_name(chat_id, name)
        return edit_dialogue

    async def delete_dialogue(self, chat_id: UUID):
        await self.db_provider.delete_dialogue(chat_id)
