from fastapi import APIRouter, Body
from uuid import UUID

from app.schemas import DialogueSchema, DialogueListSchema
from app.providers.init_providers import BOT

router = APIRouter()

@router.get("/dialogues", response_model=DialogueListSchema)
async def get_dialogue_list(user_id: UUID):
    """Получить список диалогов для user_id"""
    dialogues = await BOT.get_dialogue_list(user_id)
    return dialogues


@router.post("/dialogues", response_model=DialogueSchema)
async def create_dialogue(user_id: UUID):
    """Создать новый диалог для user_id"""
    new_dialogue = await BOT.create_dialogue(user_id)
    return new_dialogue


@router.put("/dialogues/{chat_id}", response_model=DialogueSchema)
async def change_dialogue_name(chat_id: UUID, name: str = Body(..., embed=True)):
    """Изменить диалог по chat_id"""
    edit_dialogue = await BOT.change_dialogue_name(chat_id, name)
    return edit_dialogue


@router.delete("/dialogues/{chat_id}", status_code=204)
async def delete_dialogue(chat_id: UUID):
    """Удалить диалог по chat_id"""
    await BOT.delete_dialogue(chat_id)
