from datetime import datetime
from sqlalchemy import select
from uuid import UUID, uuid4
from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.schemas import (
    DialogueSchema,
    DialoguesListSchema,
    RawMessageSchema,
    MessageSchema,
    MessagesListSchema,
    DeleteMessagesListSchema
)

# импорты моделей
from app.models import Base, DialoguePSQL


class PostgresDBProvider:
    """Провайдер для работы с базой данных PostgreSQL"""
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False, future=True)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )


    async def init_db(self):
        """Создать таблицы, если их нет"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


    async def get_dialogues_list(self, user_id: UUID) -> DialoguesListSchema:
        """Получить список диалогов по user_id"""
        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.user_id == user_id)
            )
            dialogues = result.scalars().all()
            return DialoguesListSchema(
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


    async def change_dialogue_name(self, chat_id, name) -> DialogueSchema:
        """Изменить диалог по chat_id"""
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
            dialogue.name = name
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


    async def get_messages_list(self, chat_id: UUID) -> MessagesListSchema:
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
            return MessagesListSchema(messages=messages)


    async def create_message(self, chat_id: UUID, message_data: RawMessageSchema) -> MessageSchema:
        """Создать сообщение в диалоге с chat_id"""
        async with self.SessionLocal() as session:
            message_id = str(uuid4())
            result = await session.execute(
                select(DialoguePSQL).where(DialoguePSQL.chat_id == chat_id)
            )
            dialogue = result.scalar_one_or_none()

            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )

            now = datetime.now().isoformat()
            new_message = {
                "message_id": message_id,
                "content": message_data.content,
                "created_at": now,
                "updated_at": now,
                "role": message_data.role
            }
            dialogue.messages.append(new_message)

            await session.commit()
            await session.refresh(dialogue)
            return MessageSchema.model_validate(new_message)


    async def delete_messages_list(self, chat_id: UUID, messages_id_list_to_remove: list[UUID]) -> DeleteMessagesListSchema:
        """Удалить сообщение по chat_id и списку message_id"""
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
            messages = dialogue.messages or []

            # Преобразуем входящий список UUID в список строк
            ids_to_remove = {str(u) for u in messages_id_list_to_remove}

            remaining_messages = []
            removed_ids = set()

            for message in messages:
                message_id = message.get("message_id")

                if message_id in ids_to_remove:
                    removed_ids.add(message_id)
                else:
                    remaining_messages.append(message)

            # Что реально удалили
            deleted = list(removed_ids)

            # Что не нашли
            not_found = list(ids_to_remove - removed_ids)

            # Удаление сообщений
            dialogue.messages = remaining_messages
            await session.commit()

            return { "delete": deleted, "not_found": not_found }
