from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum

class Role(str, Enum):
    """
        Роли создателя сообщения.
        User - от пользователя,
        assistant - от LLM,
        system - системный,
        tool - от инструмента (к примеру, фрагмент текста из базы знаний)
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class RawMessageSchema(BaseModel):
    """Краткая схема сообщения"""
    content: str
    role: Role


class MessageSchema(RawMessageSchema):
    """Полная схема сообщения для записи в БД"""
    message_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessagesListSchema(BaseModel):
    """Схема списка сообщений. Внутри полная схема сообщений"""
    messages: list[MessageSchema]
    
    def to_raw_messages(self) -> list[RawMessageSchema]:
        return [RawMessageSchema(content = m.content, role = m.role) for m in self.messages]


class DeleteMessagesListSchema(BaseModel):
    """
        Схема ответа при удалении сообщений из диалога.
        В delete - успешно удаленные uuid сообщений,
        в not_found - ненайденные uuid сообщений у указанного диалога
    """
    delete: list[str]
    not_found: list[str]


class DialogueSchema(BaseModel):
    """Схема диалога"""
    chat_id: UUID
    user_id: UUID
    messages: list[MessageSchema]
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DialoguesListSchema(BaseModel):
    """Схема списка диалога"""
    dialogues: list[DialogueSchema]
