from fastapi import APIRouter
from uuid import UUID

from app.schemas import (
    Role,
    RawMessageSchema,
    MessageSchema,
    MessagesListSchema,
    DeleteMessagesListSchema,
)
from app.init_providers import DATABASE

router = APIRouter()

@router.get("/messages", response_model=MessagesListSchema)
async def get_messages_list(chat_id: UUID):
    """Получить список сообщений в диалоге с chat_id"""
    messages = await DATABASE.get_messages_list(chat_id)
    return messages


@router.post("/messages/{chat_id}", response_model=MessageSchema)
async def create_message(chat_id: UUID, content: str, role: Role):
    """Создать новое сообщение в диалоге с chat_id"""
    message_data = RawMessageSchema(
        content = content,
        role = role
    )
    new_message = await DATABASE.create_message(chat_id, message_data)
    return new_message


@router.delete("/messages/{message_id}", response_model=DeleteMessagesListSchema)
async def delete_message(chat_id: UUID, message_id: UUID):
    """Удалить сообщение по chat_id и message_id"""
    response = await DATABASE.delete_messages_list(chat_id, [message_id])
    return response


@router.delete("/messages", response_model=DeleteMessagesListSchema)
async def delete_messages_list(chat_id: UUID, messages_id_list: list[UUID]):
    """Удалить список сообщений по chat_id и списка [message_id]"""
    response = await DATABASE.delete_messages_list(chat_id, messages_id_list)
    return response
