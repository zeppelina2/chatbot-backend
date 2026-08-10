from datetime import datetime
from uuid import UUID, uuid4

from app.tools.search_tool import markdown_search_tool
from app.schemas import (
    MessageSchema,
    MessageListSchema,
    RawMessageSchema,
    DeleteMessageListSchema,
    Role,
    DialogueSchema,
    DialogueListSchema
)


class Bot:
    def __init__(self, llm_provider, db_provider):
        self.llm_provider = llm_provider
        self.db_provider = db_provider

        # список инструментов
        self.tools = {
            "markdown_search_tool": markdown_search_tool,
        }

    async def process_messages(
        self,
        messages: list[RawMessageSchema],
        # максимальное количество обращений к инструментам
        # (всего, не каждого по отдельности)
        max_steps = 5
    ) -> RawMessageSchema:

        # контекст для модели
        messages_for_llm = [
            {"content": m.content, "role": m.role}
            for m in messages.messages
        ]

        # то, что вернём для записи в БД
        messages_for_base: list[MessageSchema] = []

        # счетчик шагов
        step = 0

        try:
            while step < max_steps:
                step += 1

                # обращение к LLM
                # на первом шаге на вход передаем сообщения из диалога
                # на последующих шагах передаем сообщения из: диалога, tools, системы
                response = await self.llm_provider.generate_completion_with_tools_async(messages_for_llm, self.tools)

                # добавляем ответ ассистента:
                # в контекст
                messages_for_llm.append(response.message)
                # в БД
                messages_for_base.append(
                    MessageSchema(
                        message_id=str(uuid4()),
                        content=response.message.content,
                        created_at=response.created_at,
                        updated_at=response.created_at,
                        role=Role.ASSISTANT
                    )
                )

                # если инструментов нет, то прерываем цикл
                if not response.message.tool_calls:
                    break

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
                    # в БД
                    messages_for_base.append(
                        MessageSchema(
                            message_id=str(uuid4()),
                            content=tool_content,
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            role=Role.TOOL
                        )
                    )

            return MessageListSchema(messages=messages_for_base)

        except Exception as e:
            raise Exception(f"Ошибка при запросе к Ollama: {str(e)}") from e


    async def get_message_list(self, chat_id: UUID) -> MessageListSchema:
        messages = await self.db_provider.get_message_list(chat_id)
        return messages
        
    async def create_message(self, chat_id: UUID, message: RawMessageSchema) -> MessageSchema:
        new_message = await self.db_provider.create_message(chat_id, message)
        return new_message

    async def delete_message_list(self, chat_id: UUID, message_id: UUID) -> DeleteMessageListSchema:
        response = await self.db_provider.delete_message_list(chat_id, [message_id])
        return response

    async def get_dialogue_list(self, user_id: UUID) -> DialogueListSchema:
        dialogues = await self.db_provider.get_dialogue_list(user_id)
        return dialogues

    async def create_dialogue(self, user_id: UUID) -> DialogueSchema:
        new_dialogue = await self.db_provider.create_dialogue(user_id)
        return new_dialogue

    async def change_dialogue_name(self, chat_id: UUID, name: str) -> DialogueSchema:
        edit_dialogue = await self.db_provider.change_dialogue_name(chat_id, name)
        return edit_dialogue
    
    async def delete_dialogue(self, chat_id: UUID):
        await self.db_provider.delete_dialogue(chat_id)
