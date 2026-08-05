from fastapi import APIRouter
from uuid import UUID

from app.schemas import DialogueSchema, DialoguesListSchema
from app.providers.init_providers import DATABASE

router = APIRouter()

@router.get("/dialogues", response_model=DialoguesListSchema)
async def get_dialogues_list(user_id: UUID):
    """Получить список диалогов для user_id"""
    dialogues = await DATABASE.get_dialogues_list(user_id)
    return dialogues


@router.post("/dialogues", response_model=DialogueSchema)
async def create_dialogue(user_id: UUID):
    """Создать новый диалог для user_id"""
    new_dialogue = await DATABASE.create_dialogue(user_id)
    return new_dialogue


@router.put("/dialogues/{chat_id}", response_model=DialogueSchema)
async def change_dialogue_name(chat_id: UUID, name: str):
    """Изменить диалог по chat_id"""
    edit_dialogue = await DATABASE.change_dialogue_name(chat_id, name)
    return edit_dialogue


@router.delete("/dialogues/{chat_id}", status_code=204)
async def delete_dialogue(chat_id: UUID):
    """Удалить диалог по chat_id"""
    await DATABASE.delete_dialogue(chat_id)
