from fastapi import APIRouter, Body
from uuid import UUID

from app.schemas import Role, Message, MessageListSchema, DialogueSchema
from app.providers.init_providers import BOT


router = APIRouter()


@router.post("/llm/generate_with_tools", response_model=Message)
async def generate_message_with_tools(
        chat_id: UUID, message: str = Body(..., embed=True)):
    """Отправить сообщения из диалога с chat_id в LLM с tools и получить сгенерированный ответ"""

    # сперва запишем в БД сообщение от пользователя
    await BOT.create_message(chat_id, Message(content=message, role=Role.USER))
    # запросим весь список сообщений диалога из БД
    message_list: MessageListSchema = await BOT.get_message_list(chat_id)
    messages = message_list.to_raw_messages()

    # в new_message будут сообщения для записи в БД - от tools и от LLM
    async for new_message in BOT.process_messages(messages):
        await BOT.create_message(chat_id, new_message)

    # вернем последнее сообщение от LLM
    return new_message


@router.put("/llm/generate_dialogue_name/{chat_id}", response_model=DialogueSchema)
async def generate_dialogue_name(
    chat_id: UUID,
    message: str = Body(..., embed=True)
):
    """Сгенерировать имя диалога по chat_id и первому сообщению пользователя"""
    new_dialogue_name = await BOT.generate_dialogue_name(message)
    print("new_dialogue_name: ", new_dialogue_name)
    edit_dialogue = await BOT.change_dialogue_name(chat_id, new_dialogue_name)
    
    return edit_dialogue
