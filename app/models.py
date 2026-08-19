from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

from sqlalchemy.ext.mutable import MutableList

Base = declarative_base()

class DialoguePSQL(Base):
    __tablename__ = "dialogues"

    chat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, default="Новый диалог")
    messages = Column(MutableList.as_mutable(JSON), default=list)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
