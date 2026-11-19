from typing import TypedDict

from app.tools.chunking_md_file import ChunkPath, HEADING_FIELDS, KnowledgeLibrary, MarkdownChunk, path_key


MAX_TOTAL_CONTENT_LENGTH = 15000

def _validate_path(path: ChunkPath) -> None:
    if not isinstance(path, dict) or not isinstance(path.get("fileName"), str):
        raise ValueError("Каждый путь должен быть объектом со строковым fileName.")
    if type(path.get("part")) is not int or path["part"] < 1:
        raise ValueError("Поле part должно быть целым числом от 1.")
    for field, value in path.items():
        if field in ("fileName", "part"):
            continue
        if field not in HEADING_FIELDS or not isinstance(value, str):
            raise ValueError(f"Недопустимое поле пути или значение: {field!r}.")


class ChunkSearchResult(TypedDict):
    chunks: list[MarkdownChunk]
    skipped_paths: list[ChunkPath]


# поиск чанков по путям в базе знаний
def search_chunks_by_paths(
    knowlege_library: KnowledgeLibrary,
    paths: list[ChunkPath],
) -> ChunkSearchResult:
    """
    Получить чанки по точному совпадению полных путей и пути не вместившихся чанков.
    Суммарный контент возвращаемых чанков 15000.

    Передай объекты путей из search_chunk_paths_by_word без изменений.
    Например: [{"fileName": "арка_декатрис", "h1": "#История", "part": 1}].

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
    seen: set[tuple] = set()
    total_length = 0

    for path in paths:
        _validate_path(path)
        key = path_key(path)

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
            result["skipped_paths"].append(path.copy())

    return result
