from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status

from app.providers.init_providers import BOT
from app.schemas import DialogueWithMessagesSchema, DialogueListSchema, DialogueSchema
from app.routers.auth import CurrentSession, get_current_session


router = APIRouter()
SessionDep = Annotated[CurrentSession, Depends(get_current_session)]


@router.get("/dialogues", response_model=DialogueListSchema)
async def get_dialogue_list(session: SessionDep):
    """Получить список диалогов текущего пользователя."""
    return await BOT.get_dialogue_list(user_id=session.user_id)


@router.get("/dialogue", response_model=DialogueSchema)
async def get_dialogue(chat_id: UUID, session: SessionDep):
    """Получить диалог по chat_id"""
    return await BOT.get_dialogue(chat_id, user_id=session.user_id)


@router.post("/dialogues", response_model=DialogueWithMessagesSchema)
async def create_dialogue(session: SessionDep):
    """Создать новый диалог для user_id"""
    return await BOT.create_dialogue(user_id=session.user_id)


@router.put("/dialogues/{chat_id}", response_model=DialogueSchema)
async def change_dialogue_name(
    chat_id: UUID,
    session: SessionDep,
    name: str = Body(..., embed=True),
):
    """Изменить диалог по chat_id"""
    return await BOT.change_dialogue_name(chat_id, name, user_id=session.user_id)


@router.delete("/dialogues/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dialogue(chat_id: UUID, session: SessionDep):
    """Удалить диалог по chat_id"""
    await BOT.delete_dialogue(chat_id, user_id=session.user_id)
