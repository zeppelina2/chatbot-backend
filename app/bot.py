from uuid import UUID
from collections.abc import AsyncGenerator

import yaml

from app.tools.search_tool import markdown_search_text
from app.schemas import (
    MessageSchemaBD,
    MessageListSchema,
    Message,
    DeleteMessageListSchema,
    Role,
    DialogueSchema,
    DialogueListSchema,
    Tool
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
    ) -> AsyncGenerator[Message]:

        # контекст для модели
        messages_for_llm = [
            Message(role=Role.SYSTEM, content=self.prompts["system_ecumene_prompt"]),
            *messages
        ]

        try:
            for i in range(max_steps):
                # обращение к LLM
                response = await self.llm_provider.generate_completion_with_tools_async(
                    messages_for_llm,
                    self.tools
                )

                # если в ответе tools
                if (isinstance(response, Tool)):
                    # new_message = Message(role=Role.ASSISTANT, content=self.llm_provider.tool_to_str(response))
                    # yield new_message
                    # messages_for_llm.append(new_message)
                    tool_func = self.tools.get(response.tool_name)
                    # обращаемся к инструменту
                    if not tool_func:
                        raise Exception(f"Unknown tool: {response.tool_name}")
                    result = tool_func(**response.arguments)                    
                    tool_content = str(result)
                    new_message = Message(role=Role.TOOL, content=tool_content)
                    # выбрасываем сообщение от tools, оно будет записано в базу
                    yield new_message
                    messages_for_llm.append(new_message)

                # если в ответе сообщение
                if (isinstance(response, Message)):
                    # выбрасываем сообщение от LLM, оно будет записано в базу
                    yield response
                    return
                
            # сообщение, что LLM вышла из цикла по max_steps, а не по ответу
            yield Message(role=Role.ASSISTANT, content="Не могу понять ваш запрос. Пожалуйста, попробуйте перефразировать ваш запрос.")
            return

        except Exception as e:
            raise Exception(f"Ошибка при запросе к LLM: {str(e)}") from e


    async def get_message_list(self, chat_id: UUID) -> MessageListSchema:
        messages = await self.db_provider.get_message_list(chat_id)
        return messages

    async def create_message(
        self, chat_id: UUID,
        message: Message
    ) -> MessageSchemaBD:
        new_message = await self.db_provider.create_message(chat_id, message)
        return new_message

    async def delete_message_list(
        self,
        chat_id: UUID,
        message_list: list[UUID]
    ) -> DeleteMessageListSchema:
        response = await self.db_provider.delete_message_list(chat_id, message_list)
        return response

    async def get_dialogue_list(self, user_id: UUID) -> DialogueListSchema:
        dialogues = await self.db_provider.get_dialogue_list(user_id)
        return dialogues

    async def create_dialogue(self, user_id: UUID) -> DialogueSchema:
        new_dialogue = await self.db_provider.create_dialogue(user_id)
        return new_dialogue

    async def change_dialogue_name(
        self,
        chat_id: UUID,
        name: str
    ) -> DialogueSchema:
        edit_dialogue = await self.db_provider.change_dialogue_name(chat_id, name)
        return edit_dialogue

    async def delete_dialogue(self, chat_id: UUID):
        await self.db_provider.delete_dialogue(chat_id)
