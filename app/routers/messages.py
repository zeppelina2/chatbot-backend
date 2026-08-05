from fastapi import APIRouter
from uuid import UUID

from app.schemas import (
    RawMessageSchema,
    MessageSchema,
    MessagesListSchema,
    DeleteMessagesListSchema,
)
from app.providers.init_providers import DATABASE

router = APIRouter()

@router.get("/messages/{chat_id}", response_model=MessagesListSchema)
async def get_message_list(chat_id: UUID):
    """Получить список сообщений в диалоге с chat_id"""
    messages = await DATABASE.get_message_list(chat_id)
    return messages


@router.post("/messages/{chat_id}", response_model=MessageSchema)
async def create_message(chat_id: UUID, message: RawMessageSchema):
    """Создать новое сообщение в диалоге с chat_id"""
    new_message = await DATABASE.create_message(chat_id, message)
    return new_message


@router.delete("/messages/{chat_id}/{message_id}", response_model=DeleteMessagesListSchema)
async def delete_message(chat_id: UUID, message_id: UUID):
    """Удалить сообщение по chat_id и message_id"""
    response = await DATABASE.delete_message_list(chat_id, [message_id])
    return response


@router.delete("/messages/{chat_id}", response_model=DeleteMessagesListSchema)
async def delete_message_list(chat_id: UUID, messages_id_list: list[UUID]):
    """Удалить список сообщений по chat_id и списку [message_id]"""
    response = await DATABASE.delete_message_list(chat_id, messages_id_list)
    return response
