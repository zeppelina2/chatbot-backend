from fastapi import APIRouter, Body
from uuid import UUID

from app.schemas import Role, Message, MessageListSchema
from app.providers.init_providers import BOT


router = APIRouter()


@router.post("/llm/generate_with_tools", response_model=Message)
async def generate_message_with_tools(
        chat_id: UUID, message: str = Body(..., embed=True)):
    """Отправить сообщения из диалога с chat_id в LLM с tools и получить сгенерированный ответ"""

    await BOT.create_message(chat_id, Message(content=message, role=Role.USER))
    message_list: MessageListSchema = await BOT.get_message_list(chat_id)
    messages = message_list.to_raw_messages()

    async for new_message in BOT.process_messages(messages):
        await BOT.create_message(chat_id, new_message)

    return new_message
