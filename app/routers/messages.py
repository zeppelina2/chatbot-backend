from fastapi import APIRouter
from uuid import UUID

from app.schemas import (
    Message,
    MessageSchemaBD,
    MessageListSchema,
    DeleteMessageListSchema,
)
from app.providers.init_providers import BOT

router = APIRouter()


@router.get("/messages/{chat_id}", response_model=MessageListSchema)
async def get_message_list(chat_id: UUID):
    """Получить список сообщений в диалоге с chat_id"""
    messages = await BOT.get_message_list(chat_id)
    return messages


@router.get("/messages/{chat_id}/user-assistant", response_model=MessageListSchema)
async def get_message_list(chat_id: UUID):
    """Получить список сообщений от user и assistant в диалоге с chat_id"""
    messages = await BOT.get_message_list_for_front(chat_id)
    return messages


@router.post("/messages/{chat_id}", response_model=MessageSchemaBD)
async def create_message(chat_id: UUID, message: Message):
    """Создать новое сообщение в диалоге с chat_id"""
    new_message = await BOT.create_message(chat_id, message)
    return new_message


@router.delete("/messages/{chat_id}/{message_id}",
               response_model=DeleteMessageListSchema)
async def delete_message(chat_id: UUID, message_id: UUID):
    """Удалить сообщение по chat_id и message_id"""
    response = await BOT.delete_message_list(chat_id, [message_id])
    return response


@router.delete("/messages/{chat_id}", response_model=DeleteMessageListSchema)
async def delete_message_list(chat_id: UUID, messages_id_list: list[UUID]):
    """Удалить список сообщений по chat_id и списку [message_id]"""
    response = await BOT.delete_message_list(chat_id, messages_id_list)
    return response
