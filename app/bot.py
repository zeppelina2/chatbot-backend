from uuid import UUID
from collections.abc import AsyncGenerator
import yaml

from app.schemas import (
    MessageSchemaBD,
    MessageListSchema,
    Message,
    DeleteMessageListSchema,
    Role,
    DialogueWithMessagesSchema,
    DialogueSchema,
    DialogueListSchema,
    Tool
)

from app.tools.chunking_md_file import create_knowlege_library_from_markdown, save_chunks
from app.tools.search_chunks_by_paths_tool import search_chunks_by_paths, ChunkSearchResult
from app.tools.search_paths_by_word_tool import search_chunk_paths_by_word


class Bot:
    def __init__(self, llm_provider, db_provider, doc_path_list):
        self.llm_provider = llm_provider
        self.db_provider = db_provider

        # база знаний
        self.knowlege_library, headings_tree = create_knowlege_library_from_markdown(doc_path_list)

        with open("app/prompts.yaml") as file:
            self.prompts = yaml.safe_load(file)["prompts"]

        # в системный промпт добавим дерево заголовков базы знаний
        self.prompts["system_ecumene_prompt"] = self.prompts["system_ecumene_prompt"].replace(
            "{headings_tree}",
            headings_tree,
        )

        # список инструментов
        self.tools = {
            "search_chunks_by_paths": self.search_chunks_by_paths,
            "search_chunk_paths_by_word": self.search_chunk_paths_by_word,
        }
        
        # print("headings_tree: ", headings_tree)
        
        # items = [['арка_декатрис', '#26.04.2026 г. Сессия 11. Храм весны', '##Разговор Трис и Корвуса'], ['арка_декатрис', '#26.04.2026 г. Сессия 11. Храм весны', '##Башар Махди']]
        # resp = self.search_chunks_by_paths(items)
        # print("Получить чанки по списку путей", resp)


    def search_chunks_by_paths(self, paths: list[list[str]]) -> ChunkSearchResult:
        """
        Получить чанки по точному совпадению полных путей и пути не вместившихся чанков.
        Суммарный контент возвращаемых чанков 15000.
        
        paths - список путей.
        Каждый путь является списком и содержит первым элементом префикс, далее идут заголовки с символами #.
        Последним элементом может быть номер части вида "часть n", если связный текст был разделен на чанки.

        Пример, если связный текст разбит на несколько чанков, то в конце пути прописан номер части:
        [["арка_декатрис", "#История", "##Анатийские войны", "часть 1"]]
        [["арка_декатрис", "#История", "##Анатийские войны", "часть 2"]]
        Пример, если связный текст поместился в чанк полностью, часть в нем не пишется:
        [["арка_декатрис", "#История", "##Последствия"]]

        Результат следует порядку запрошенных путей.
        Неизвестные пути пропускаются, повторные пути игнорируются.
        Если одному пути соответствуют несколько чанков,
        возвращаются все они в порядке исходного документа.
        Чанки, не помещающиеся в оставшийся лимит, пропускаются.
        Содержимое чанков не обрезается.
        """
        return search_chunks_by_paths(
            knowlege_library=self.knowlege_library,
            paths=paths,
        )


    def search_chunk_paths_by_word(
        self,
        search_str: str = "",
        full_word: bool = False,
        case_sensitive: bool = False,
        regex: str = "",
    ) -> list[list[str]]:
        """
        Найти пути чанков по тексту или регулярному выражению.
    
        search_str: строка для поиска.
        regex: непустое выражение имеет приоритет над search_str.
        full_word: запрещает соседние буквы, цифры и подчёркивания.
        case_sensitive: включает учёт регистра.

        Поиск выполняется только по содержимому chunk.
        Пустой запрос возвращает пустой список.
        Каждый найденный путь возвращается один раз.
        """
        return search_chunk_paths_by_word(
            knowlege_library=self.knowlege_library,
            search_str=search_str,
            full_word=full_word,
            case_sensitive=case_sensitive,
            regex=regex,
        )


    async def process_messages(
        self,
        messages: list[Message],
        # максимальное количество обращений к инструментам
        # (всего, не каждого по отдельности)
        max_steps=10
    ) -> AsyncGenerator[Message]:

        # контекст для модели
        messages_for_llm = [
            Message(
                role=Role.SYSTEM,
                content=self.prompts["system_ecumene_prompt"]),
            *messages
        ]

        try:
            for i in range(max_steps):
                print("ИТЕРАЦИЯ: ", i)
                print("\n")
                # обращение к LLM
                response = await self.llm_provider.generate_completion_with_tools_async(
                    messages_for_llm,
                    self.tools,
                )

                # если в ответе tools
                if (isinstance(response, Tool)):
                    tool_func = self.tools.get(response.tool_name)
                    # обращаемся к инструменту
                    if not tool_func:
                        raise Exception(f"Unknown tool: {response.tool_name}")

                    # сохраняем запрос ассистента на вызов инструмента
                    assistant_tool_call = self.llm_provider.tool_to_assistant_message(response)
                    messages_for_llm.append(assistant_tool_call)
                    yield assistant_tool_call

                    print("response.tool_name: ", response.tool_name)
                    print("\n")
                    print("response.arguments for tool: ", response.arguments)
                    print("\n")
                    result = tool_func(**response.arguments)
                    print("tool result: ", result)
                    print("\n")
                    tool_content = str(result)
                    new_message = Message(role=Role.TOOL, content=tool_content, tool_call_id=response.tool_call_id)
                    # выбрасываем сообщение от tools, оно будет записано в базу
                    yield new_message
                    messages_for_llm.append(new_message)

                # если в ответе сообщение
                if (isinstance(response, Message)):
                    # выбрасываем сообщение от LLM, оно будет записано в базу
                    yield response
                    return

            # сообщение, что LLM вышла из цикла по max_steps, а не по ответу
            yield Message(role=Role.ASSISTANT, content="Не могу понять ваш запрос. Пожалуйста, попробуйте перефразировать.")
            return

        except Exception as e:
            raise Exception(f"Ошибка при запросе к LLM: {str(e)}") from e


    # =================== CRUD =================== #

    async def get_message_list(self, chat_id: UUID) -> MessageListSchema:
        messages = await self.db_provider.get_message_list(chat_id)
        return messages


    async def get_message_user_assistant_list(self, chat_id: UUID) -> MessageListSchema:
        messages = await self.db_provider.get_message_user_assistant_list(chat_id)
        return messages


    async def create_message(
        self, chat_id: UUID,
        message: Message
    ) -> MessageSchemaBD:
        new_message = await self.db_provider.create_message(chat_id, message)
        return new_message


    async def delete_message_list(
        self,
        chat_id: UUID,
        message_list: list[UUID]
    ) -> DeleteMessageListSchema:
        response = await self.db_provider.delete_message_list(chat_id, message_list)
        return response


    async def get_dialogue_list(
        self,
        user_id: UUID
    ) -> DialogueListSchema:
        dialogues = await self.db_provider.get_dialogue_list(user_id)
        return dialogues


    async def get_dialogue(
        self,
        chat_id: UUID
    ) -> DialogueListSchema:
        dialogues = await self.db_provider.get_dialogue(chat_id)
        return dialogues


    async def create_dialogue(
        self,
        user_id: UUID
    ) -> DialogueWithMessagesSchema:
        new_dialogue = await self.db_provider.create_dialogue(user_id)
        return new_dialogue


    async def change_dialogue_name(
        self,
        chat_id: UUID,
        name: str
    ) -> DialogueSchema:
        edit_dialogue = await self.db_provider.change_dialogue_name(chat_id, name)
        return edit_dialogue


    async def generate_dialogue_name(self, message: str) -> DialogueListSchema:
        new_dialogue_name = await self.llm_provider.generate_dialogue_name_async(message)
        return new_dialogue_name


    async def delete_dialogue(self, chat_id: UUID) -> None:
        await self.db_provider.delete_dialogue(chat_id)
