import re

from app.tools.chunking_md_file import MarkdownChunk

def search_chunk_paths_by_word(
    knowlege_library: dict[tuple[str, ...], list[MarkdownChunk]],
    search_str: str = "",
    full_word: bool = False,
    case_sensitive: bool = False,
    regex: str = "",
) -> list[list[str]]:
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

    return [
        list(path)
        for path, chunks in knowlege_library.items()
        if any(
            compiled_pattern.search(chunk["chunk"]) is not None
            for chunk in chunks
        )
    ]
