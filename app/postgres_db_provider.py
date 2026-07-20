from datetime import datetime
from sqlalchemy import select
from uuid import UUID, uuid4
from fastapi import HTTPException, status
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.schemas import DialogueSchema, DialoguesSchema, DialogueChangeNameSchema, MessageSchema, MessagesSchema, CreateMessageSchema

# импорты моделей
from app.models import Base, DialoguePSQL


class PostgresDBProvider:
    """Провайдер для работы с базой данных PostgreSQL"""
    def __init__(self, DATABASE_URL: str):
        self.engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )


    async def init_db(self):
        print("INIT DB CALLED")
        """Создать таблицы, если их нет"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


    async def get_dialogues(self, user_id: UUID) -> DialoguesSchema:
        """Получить список диалогов по user_id"""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.user_id == user_id)
            )
            dialogues = result.scalars().all()
            return DialoguesSchema(
                dialogues = [
                    DialogueSchema.model_validate(dialogue) for dialogue in dialogues
                ]
            )


    async def create_dialogue(self, user_id: UUID) -> DialogueSchema:
        """Создать диалог по user_id"""
        async with self.SessionLocal() as session:
            chat_id = str(uuid4())
            dialogue = DialoguePSQL(
                chat_id=chat_id,
                user_id=user_id,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(dialogue)
            await session.commit()
            await session.refresh(dialogue)
            return DialogueSchema.model_validate(dialogue)


    async def change_dialogue_name(self, dialogue_data: DialogueChangeNameSchema) -> DialogueSchema:
        """Изменить диалог по chat_id"""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.chat_id == dialogue_data.chat_id)
            )
            dialogue = result.scalar_one_or_none()
            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )
            dialogue.name = dialogue_data.name
            dialogue.updated_at = datetime.now()
            
            await session.commit()
            await session.refresh(dialogue)
            return DialogueSchema.model_validate(dialogue)


    async def delete_dialogue(self, chat_id: UUID):
        """Удалить диалог по chat_id"""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.chat_id == chat_id)
            )
            dialogue = result.scalar_one_or_none()
            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )
            await session.delete(dialogue)
            await session.commit()


    async def get_messages(self, chat_id: UUID) -> MessagesSchema:
        """Получить список сообщений в диалоге с chat_id"""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.chat_id == chat_id)
            )
            dialogue = result.scalar_one_or_none()
            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )
            messages = dialogue.messages
            return MessagesSchema(
                messages = [
                    MessageSchema.model_validate(message) for message in messages
                ]
            )


    async def create_message(self, message_data: CreateMessageSchema) -> MessageSchema:
        """Создать сообщение в диалоге с chat_id"""
        async with self.SessionLocal() as session:
            message_id = str(uuid4())
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.chat_id == message_data.chat_id)
            )
            dialogue = result.scalar_one_or_none()
            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )
            dialogue.messages.append({
                "message_id": message_id,
                "content": message_data.content,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "role": message_data.role
            })
            
            print("dialogue.messages: ", dialogue.messages)

            await session.commit()
            await session.refresh(dialogue)
            print("dialogue.messages 2: ", dialogue.messages)
            return MessageSchema.model_validate(dialogue.messages)


    async def delete_messages(self, chat_id: UUID, messages_id_list: list[UUID]) -> dict[Any, Any]:
        """Удалить сообщение по chat_id и message_id"""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.chat_id == chat_id)
            )
            dialogue = result.scalar_one_or_none()
            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )
            messages = dialogue.messages

            # Проверка: все ли id из messages_id_list существуют в dialogue.messages
            remaining_messages = []
            for m in messages:
                if m.message_id in messages_id_list:
                    messages_id_list.remove(m.message_id)
                else:
                    remaining_messages.append(m)
            if len(messages_id_list) != 0:
                return { "type": "error", "error": f"Messages {messages_id_list} not found" }

            # Удаление сообщений
            dialogue.messages = remaining_messages
            await session.commit()
            return { "type": "success" }
