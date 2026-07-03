from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class MessageSchema(BaseModel):
    message_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
    role: str

    class Config:
        from_attributes = True

class DialogueSchema(BaseModel):
    chat_id: UUID
    user_id: UUID
    messages: list[MessageSchema]
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DialoguesSchema(BaseModel):
    dialogues: list[DialogueSchema]

class MessagesSchema(BaseModel):
    messages: list[MessageSchema]

class DialogueChangeNameSchema(BaseModel):
    chat_id: UUID
    name: str
