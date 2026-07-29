from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class MessageSchema(BaseModel):
    # тут хорошо добавить еще chat_id
    message_id: str
    content: str
    created_at: str
    updated_at: str
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

class DialogueChangeNameSchema(BaseModel):
    chat_id: UUID
    name: str

class MessageListSchema(BaseModel):
    messages: list[MessageSchema]
    
class CreateMessageSchema(BaseModel): # вместо этого использовать MessageSchema
    chat_id: UUID
    content: str
    role: str

class RequestMessageDataSchema(BaseModel): # вместо этого использовать MessageSchema 
    chat_id: UUID
    content: str

class DeleteMessageListSchema(BaseModel):
    delete: list[str]
    not_found: list[str]
