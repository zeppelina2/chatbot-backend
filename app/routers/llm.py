from fastapi import APIRouter
from uuid import UUID

from app.schemas import Role, MessageSchema
from app.init_providers import DATABASE, LLM_PROVIDER
from app.routers.messages import create_message

router = APIRouter()

@router.post("/llm/generate", response_model=MessageSchema)
async def generate_message(chat_id: UUID):
    """Отправить сообщения из диалога с chat_id в LLM и получить сгенерированный ответ"""
    messages = await DATABASE.get_messages_list(chat_id)
 
    llm_message = await LLM_PROVIDER.generate_completion_async(messages)
    
    await create_message(chat_id, llm_message.content, Role.ASSISTANT)

    return llm_message
