from fastapi import APIRouter, Body
from uuid import UUID

from app.schemas import Role, RawMessageSchema, MessageListSchema
from app.providers.init_providers import BOT


router = APIRouter()

@router.post("/llm/generate_with_tools", response_model=MessageListSchema)
async def generate_message_with_tools(chat_id: UUID, message: str = Body(..., embed=True)):
    """Отправить сообщения из диалога с chat_id в LLM с tools и получить сгенерированный ответ"""
    await BOT.create_message(chat_id, RawMessageSchema(content=message, role=Role.USER))
    messages = await BOT.get_message_list(chat_id)
 
    llm_response = await BOT.process_messages(messages)

    return llm_response
