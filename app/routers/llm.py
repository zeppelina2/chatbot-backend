from fastapi import APIRouter
from uuid import UUID

from app.schemas import MessageSchema, RequestMessageDataSchema
from app.init_providers import DATABASE, LLM_PROVIDER
from app.routers.messages import create_message_from_assistant

router = APIRouter()

@router.post("/llm/generate", response_model=MessageSchema)
async def generate_message(chat_id: UUID):
    """Отправить сообщения из диалога с chat_id в LLM и получить сгенерированный ответ"""
    messages = await DATABASE.get_messages(chat_id)
 
    llm_message = await LLM_PROVIDER.generate_async(messages)
    
    print("llm_message", llm_message)
    
    await create_message_from_assistant(RequestMessageDataSchema(chat_id=chat_id, content=llm_message.content))

    return llm_message
