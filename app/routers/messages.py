from fastapi import APIRouter, HTTPException
from uuid import UUID, uuid4

from app.dialogue import MessageSchema
from app.database import DATABASE

router = APIRouter()

@router.get("/messages", response_model=list[MessageSchema])
async def list_messages(chat_id: UUID):
    """Получить список сообщений в диалоге с chat_id"""
    messages = await DATABASE.get_messages(chat_id)
    return messages


@router.post("/messages", response_model=MessageSchema)
async def create_message(chat_id: UUID):
    """Создать новое сообщение в диалоге с chat_id"""
    message_id = str(uuid4())
    new_message = await DATABASE.create_message(chat_id, message_id)
    return new_message


@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(chat_id: UUID, message_id: UUID):
    """Удалить сообщение по chat_id и message_id"""
    success = await DATABASE.delete_messages(chat_id, [message_id])
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")


@router.delete("/messages", status_code=204)
async def delete_message_list(chat_id: UUID, messages_id_list: list[UUID]):
    """Удалить список сообщений по chat_id и списка [message_id]"""
    response = await DATABASE.delete_messages(chat_id, messages_id_list)
    if response.type == "error":
        raise HTTPException(status_code=404, detail=f"Message {response.error_messages_id_list} not found")
