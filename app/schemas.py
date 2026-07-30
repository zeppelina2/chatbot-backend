from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class RawMessageSchema(BaseModel):
    content: str
    role: Role


class MessageSchema(RawMessageSchema):
    message_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessagesListSchema(BaseModel):
    messages: list[MessageSchema]
    
    def to_raw_messages(self) -> list[RawMessageSchema]:
        return [RawMessageSchema(content = message.content, role = message.role) for message in self.messages]


class DeleteMessagesListSchema(BaseModel):
    delete: list[str]
    not_found: list[str]


class DialogueSchema(BaseModel):
    chat_id: UUID
    user_id: UUID
    messages: list[MessageSchema]
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DialoguesListSchema(BaseModel):
    dialogues: list[DialogueSchema]
