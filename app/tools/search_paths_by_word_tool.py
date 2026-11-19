import re

from app.tools.chunking_md_file import ChunkPath, HEADING_FIELDS, KnowledgeLibrary


def search_chunk_paths_by_word(
    knowlege_library: KnowledgeLibrary,
    search_str: str = "",
    full_word: bool = False,
    case_sensitive: bool = False,
    regex: str = "",
) -> list[ChunkPath]:
    """
    Найти пути чанков по тексту или регулярному выражению.
    
    regex: непустое выражение имеет приоритет над search_str.
    full_word: запрещает соседние буквы, цифры и подчёркивания.
    case_sensitive: включает учёт регистра.

    Поиск выполняется только по содержимому chunk.
    Пустой запрос возвращает пустой список.
    Каждый найденный путь возвращается один раз.
    """

    if regex:
        pattern = regex
    else:
        query = search_str.strip()

        if not query:
            return []

        # Специальные символы в обычном запросе ищем буквально.
        pattern = re.escape(query)

    if full_word:
        pattern = rf"(?<!\w)(?:{pattern})(?!\w)"

    flags = 0 if case_sensitive else re.IGNORECASE
    compiled_pattern = re.compile(pattern, flags)

    matched_paths: list[ChunkPath] = []

    for chunks in knowlege_library.values():
        # Все чанки в этой группе имеют одинаковый путь.
        path = chunks[0]["path"]

        if any(
            compiled_pattern.search(path[field])
            for field in HEADING_FIELDS
            if field in path
        ):
            matched_paths.append(path.copy())
            continue

        if any(compiled_pattern.search(chunk["chunk"]) for chunk in chunks):
            matched_paths.append(path.copy())

    return matched_paths
