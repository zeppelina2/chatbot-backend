from typing import TypedDict

from app.tools.chunking_md_file import MarkdownChunk


MAX_TOTAL_CONTENT_LENGTH = 15000


class ChunkSearchResult(TypedDict):
    chunks: list[MarkdownChunk]
    skipped_paths: list[list[str]]


# поиск чанков по путям в базе знаний
def search_chunks_by_paths(
    knowlege_library: dict[tuple[str, ...], list[MarkdownChunk]],
    paths: list[list[str]],
) -> ChunkSearchResult:
    """
    Получить чанки по точному совпадению полных путей и пути не вместившихся чанков.
    Суммарный контент возвращаемых чанков 15000.

    Каждый путь содержит заголовки с символами # и номер
    части строкой в последнем элементе.

    Пример:
    [["#История", "##Анатийские войны", "2"]]

    Результат следует порядку запрошенных путей.
    Неизвестные пути пропускаются, повторные пути игнорируются.
    Если одному пути соответствуют несколько чанков,
    возвращаются все они в порядке исходного документа.
    Чанки, не помещающиеся в оставшийся лимит, пропускаются.
    Содержимое чанков не обрезается.
    """
    result: ChunkSearchResult = {
        "chunks": [],
        "skipped_paths": [],
    }
    seen: set[tuple[str, ...]] = set()
    total_length = 0

    for path in paths:
        key = tuple(path)

        if key in seen:
            continue

        seen.add(key)
        has_skipped_chunks = False

        for chunk in knowlege_library.get(key, []):
            content_length = len(chunk["chunk"])

            if total_length + content_length > MAX_TOTAL_CONTENT_LENGTH:
                has_skipped_chunks = True
                continue

            result["chunks"].append(chunk)
            total_length += content_length

        if has_skipped_chunks:
            result["skipped_paths"].append(list(key))

    return result
