from app.search_tool import markdown_search_tool
from datetime import datetime

    # async def generate_completion_async(self, messages: list[RawMessage]) -> RawMessage:
    #     messages_for_llm = [
    #       {"content": message.content, "role": message.role} for message in messages.messages
    #     ]
        
    #     messages_for_base = []

    #     try:
    #         # первое обращение с промптом от пользователя
    #         response = await self.async_client.chat(
    #             model=self.ollama_model,
    #             messages=messages_for_llm,
    #             tools=[markdown_search_tool]
    #             # think=True
    #         )

    #         # добавим результат к сообщениям для llm и к сообщениям для БД
    #         messages_for_llm.append(response.message)
    #         messages_for_base.append(self.format_llm_response_for_bd(response, "assistant"))

    #         # если в сообщении от llm есть tool_calls, то обращаемся к инструменту
    #         if response.message.tool_calls:
    #             call = response.message.tool_calls[0]
    #             # обращаемся к инструменту
    #             result = markdown_search_tool(**call.function.arguments)
    #             # добавим результат инструмента к сообщениям для llm и к сообщениям для БД
    #             tool_resp_content = str(result)
    #             messages_for_llm.append({ "role": "tool", "tool_name": call.function.name, "content": tool_resp_content })
    #             messages_for_base.append(MessageSchema(
    #                 message_id = str(uuid4()),
    #                 content = tool_resp_content,
    #                 created_at = datetime.now(),
    #                 updated_at = datetime.now(),
    #                 role = "tool"
    #             ))
            
    #             # обращение к llm уже с сообщением от инструмента
    #             tool_response = await self.async_client.chat(
    #                 model=self.ollama_model,
    #                 messages=messages_for_llm,
    #                 tools=[markdown_search_tool]
    #                 # think=True
    #             )

    #             messages_for_llm.append(tool_response.message)
    #             messages_for_base.append(self.format_llm_response_for_bd(tool_response, "assistant"))

    #         return MessagesListSchema(messages=messages_for_base)
    #     except Exception as e:
    #         raise Exception(f"Ошибка при запросе к Ollama: {str(e)}") from e




    # def format_llm_response_for_bd(self, response, role: str) -> MessageSchema:
    #     return MessageSchema(
    #         message_id = str(uuid4()),
    #         content = response.message.content,
    #         created_at = response.created_at,
    #         updated_at = response.created_at,
    #         role = role
    #     )
