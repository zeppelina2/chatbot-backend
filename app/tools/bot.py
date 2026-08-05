from datetime import datetime
from uuid import uuid4

from app.tools.search_tool import markdown_search_tool
from app.schemas import MessageSchema, MessagesListSchema, RawMessageSchema, Role


async def generate_completion_async(
    self,
    messages: list[RawMessageSchema]
) -> RawMessageSchema:

    # контекст для модели
    messages_for_llm = [
        {"content": m.content, "role": m.role}
        for m in messages.messages
    ]

    # то, что вернём для записи в БД
    messages_for_base: list[MessageSchema] = []

    # защита от бесконечного цикла
    MAX_STEPS = 5
    # счетчик шагов
    step = 0

    try:
        while step < MAX_STEPS:
            step += 1

            # обращение к LLM
            # на первом шаге на вход передаем сообщения из диалога
            # на последующих шагах передаем сообщения из: диалога, tools, системы
            response = await self.async_client.chat(
                model=self.ollama_model,
                messages=messages_for_llm,
                tools=[markdown_search_tool],
                think=True
            )

            # добавляем ответ ассистента
            messages_for_llm.append(response.message)
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

            # если в сообщении от llm есть tool_calls, то обращаемся к инструментам
            # (их может быть несколько, обработаем их в цикле)
            for call in response.message.tool_calls:
                tool_name = call.function.name
                args = call.function.arguments

                # обращаемся к инструменту
                if tool_name == "markdown_search_tool":
                    result = markdown_search_tool(**args)
                else:
                    result = f"Unknown tool: {tool_name}"

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

        return MessagesListSchema(messages=messages_for_base)

    except Exception as e:
        raise Exception(f"Ошибка при запросе к Ollama: {str(e)}") from e
