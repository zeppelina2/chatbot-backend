from fastapi import APIRouter
from uuid import UUID
from datetime import datetime

from app.schemas import MessageListSchema, MessageSchema, CreateMessageSchema
from app.init_providers import DATABASE, LLM_PROVIDER

router = APIRouter()

@router.post("/llm/generate", response_model=MessageListSchema)
async def generate_message(chat_id: UUID, messages: MessageSchema):
    """Отправить сообщения из диалога с chat_id в LLM и получить сгенерированный ответ"""
    messages = await DATABASE.get_messages(chat_id)
    
    llm_response = await LLM_PROVIDER.generate_async(messages)
    now = datetime.now().isoformat()

    message_from_llm = CreateMessageSchema(
        chat_id = chat_id,
        content = llm_response,
        created_at=now,
        updated_at=now,
        role = "agent"
    )

    return message_from_llm
