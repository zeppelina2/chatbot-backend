from fastapi import APIRouter
from uuid import UUID

from app.schemas import (
    MessageSchema,
    RequestMessageDataSchema,
    CreateMessageSchema,
    MessageListSchema,
    DeleteMessageListSchema
)
from app.init_providers import DATABASE

router = APIRouter()

@router.get("/messages", response_model=MessageListSchema)
async def list_messages(chat_id: UUID):
    """Получить список сообщений в диалоге с chat_id"""
    messages = await DATABASE.get_messages(chat_id)
    return messages


@router.post("/messages/user", response_model=MessageSchema)
async def create_message_from_user(req_message_data: RequestMessageDataSchema):
    """Создать новое сообщение от пользователя в диалоге с chat_id"""
    message_data = CreateMessageSchema(
        chat_id = req_message_data.chat_id,
        content = req_message_data.content,
        role = "user"
    )
    new_message = await DATABASE.create_message(message_data)
    return new_message


@router.post("/messages/agent", response_model=MessageSchema)
async def create_message_from_agent(req_message_data: RequestMessageDataSchema):
    """Создать новое сообщение от агента в диалоге с chat_id"""
    message_data = CreateMessageSchema(
        chat_id=req_message_data.chat_id,
        content=req_message_data.content,
        role="agent"
    )
    new_message = await DATABASE.create_message(message_data)
    return new_message


@router.post("/messages/system", response_model=MessageSchema)
async def create_message_from_system(req_message_data: RequestMessageDataSchema):
    """Создать новое системное сообщение в диалоге с chat_id"""
    message_data = CreateMessageSchema(
        chat_id=req_message_data.chat_id,
        content=req_message_data.content,
        role="system"
    )
    new_message = await DATABASE.create_message(message_data)
    return new_message


@router.delete("/messages/{message_id}", response_model=DeleteMessageListSchema)
async def delete_message(chat_id: UUID, message_id: UUID):
    """Удалить сообщение по chat_id и message_id"""
    response = await DATABASE.delete_message_list(chat_id, [message_id])
    return response


@router.delete("/messages", response_model=DeleteMessageListSchema)
async def delete_message_list(chat_id: UUID, messages_id_list: list[UUID]):
    """Удалить список сообщений по chat_id и списка [message_id]"""
    response = await DATABASE.delete_message_list(chat_id, messages_id_list)
    return response
