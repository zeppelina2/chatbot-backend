from datetime import datetime
from sqlalchemy import select, update
from uuid import UUID, uuid4
from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.schemas import (
    DialogueWithMessagesSchema,
    DialogueListSchema,
    DialogueSchema,
    Message,
    MessageSchemaBD,
    MessageListSchema,
    DeleteMessageListSchema,
    Role
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


    async def get_dialogue_list(self, user_id: UUID) -> DialogueListSchema:
        """Получить список диалогов по user_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                select(
                    DialoguePSQL.chat_id,
                    DialoguePSQL.user_id,
                    DialoguePSQL.name,
                    DialoguePSQL.created_at,
                    DialoguePSQL.updated_at,
                )
                .where(
                    DialoguePSQL.user_id == user_id,
                    DialoguePSQL.active.is_(True),
                )
                .order_by(DialoguePSQL.updated_at.desc())
            )

            dialogues = result.all()

            return DialogueListSchema(
                dialogues=[
                    DialogueSchema.model_validate(dialogue)
                    for dialogue in dialogues
                ]
            )


    async def get_dialogue(self, chat_id: UUID) -> DialogueListSchema:
        """Получить диалог по chat_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                select(
                    DialoguePSQL.chat_id,
                    DialoguePSQL.user_id,
                    DialoguePSQL.name,
                    DialoguePSQL.created_at,
                    DialoguePSQL.updated_at,
                )
                .where(DialoguePSQL.chat_id == chat_id)
            )

            dialogue = result.one_or_none()

            return DialogueSchema.model_validate(dialogue)


    async def create_dialogue(
        self,
        user_id: UUID
    ) -> DialogueWithMessagesSchema:
        """Создать диалог по user_id"""

        async with self.SessionLocal() as session:
            chat_id = uuid4()
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

            return DialogueWithMessagesSchema(
                chat_id=dialogue.chat_id,
                user_id=dialogue.user_id,
                messages=[],
                name=dialogue.name,
                created_at=dialogue.created_at,
                updated_at=dialogue.updated_at,
            )


    async def change_dialogue_name(
        self,
        chat_id,
        name
    ) -> DialogueSchema:
        """Изменить имя диалога по chat_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                update(DialoguePSQL)
                .where(DialoguePSQL.chat_id == chat_id)
                .values(
                    name=name,
                    updated_at=datetime.now(),
                )
                .returning(
                    DialoguePSQL.chat_id,
                    DialoguePSQL.user_id,
                    DialoguePSQL.name,
                    DialoguePSQL.created_at,
                    DialoguePSQL.updated_at,
                )
            )

            dialogue = result.one_or_none()

            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )

            await session.commit()

            return DialogueSchema.model_validate(dialogue)


    async def delete_dialogue(self, chat_id: UUID) -> None:
        """Удалить диалог по chat_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                update(DialoguePSQL)
                .where(DialoguePSQL.chat_id == chat_id)
                .values(
                    active=False,
                    updated_at=datetime.now(),
                )
                .returning(
                    DialoguePSQL.chat_id,
                    DialoguePSQL.active,
                )
            )
            
            dialogue = result.one_or_none()
            
            if not dialogue:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )

            await session.commit()


    async def get_message_list(self, chat_id: UUID) -> MessageListSchema:
        """Получить список сообщений в диалоге с chat_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL.messages)
                .where(DialoguePSQL.chat_id == chat_id)
            )

            messages = result.scalar_one_or_none()

            if messages is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )

            return MessageListSchema(
                messages=[
                    MessageSchemaBD.model_validate(message)
                    for message in messages
                ]
            )


    async def get_message_list_for_front(self, chat_id: UUID) -> MessageListSchema:
        """Получить список сообщений в диалоге с chat_id"""

        messages_list = await self.get_message_list(chat_id=chat_id)

        return MessageListSchema(
            messages=[
                MessageSchemaBD.model_validate(message)
                for message in messages_list.messages
                if message.role in (Role.USER, Role.ASSISTANT) and message.content
            ]
        )


    async def create_message(
        self,
        chat_id: UUID,
        message_data: Message
    ) -> MessageSchemaBD:
        """Создать сообщение в диалоге с chat_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL.messages)
                .where(DialoguePSQL.chat_id == chat_id)
            )

            messages = result.scalar_one_or_none()

            if messages is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )

            now = datetime.now().isoformat()

            new_message = {
                "message_id": str(uuid4()),
                "content": message_data.content,
                "created_at": now,
                "updated_at": now,
                "role": message_data.role,
            }
            
            if message_data.tool_calls:
                new_message["tool_calls"] = message_data.tool_calls

            if message_data.tool_call_id:
                new_message["tool_call_id"] = message_data.tool_call_id

            messages.append(new_message)
            
            await session.execute(
                update(DialoguePSQL)
                .where(DialoguePSQL.chat_id == chat_id)
                .values(
                    messages=messages,
                    updated_at=datetime.now(),
                )
            )

            await session.commit()

            return MessageSchemaBD.model_validate(new_message)


    async def delete_message_list(
        self,
        chat_id: UUID,
        messages_id_list_to_remove: list[UUID]
    ) -> DeleteMessageListSchema:
        """Удалить сообщение по chat_id и списку message_id"""

        async with self.SessionLocal() as session:
            result = await session.execute(
                select(DialoguePSQL.messages)
                .where(DialoguePSQL.chat_id == chat_id)
            )

            messages = result.scalar_one_or_none()

            if messages is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dialogue with given chat_id not found"
                )

            # Преобразуем входящий список UUID в список строк
            ids_to_remove = { str(message_id) for message_id in messages_id_list_to_remove }

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
            await session.execute(
                update(DialoguePSQL)
                .where(DialoguePSQL.chat_id == chat_id)
                .values(
                    messages=remaining_messages,
                    updated_at=datetime.now(),
                )
            )

            await session.commit()

            return { "delete": deleted, "not_found": not_found }
