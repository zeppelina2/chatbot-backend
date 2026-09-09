import re
from pathlib import Path

def markdown_search_text(
    search_str: str,
    chunk_size: int = 100,
    case_sensitive: bool = False,
    full_word: bool = False,
    regex: str = "",
    offset: int = 0,
) -> list[str]:
    """
    Ищет текст в Markdown-файле и возвращает не более 10 чанков.

    В строке поиска имеет смысл использовать stemming.

    Режимы поиска:
    - По умолчанию ищет полное вхождение search_str в текст.
    - При full_word=True ищет search_str как отдельное слово.
    - Если передан regex, поиск выполняется по регулярному выражению,
      а search_str и full_word игнорируются.
    - При case_sensitive=True учитывает регистр.

    Пагинация:
    - offset — количество найденных совпадений, которые нужно пропустить.
    - Возвращается не более 10 совпадений после offset.

    Размер чанка:
    - chunk_size символов до совпадения;
    - найденный текст;
    - chunk_size символов после совпадения;
    - максимальный chunk_size — 1000.
    """

    md_path = Path("app/resources/ecumene.md")

    # Проверяем крайние случаи:
    if not md_path.is_file():
        return []

    if not 0 <= chunk_size <= 1000:
        raise ValueError("chunk_size должен быть в диапазоне от 0 до 1000")

    if offset < 0:
        raise ValueError("offset не может быть отрицательным")

    if not regex and not search_str:
        raise ValueError("Необходимо передать search_str или regex")

    # Если проверки прошли, работаем с текстом:
    text = md_path.read_text(encoding="utf-8")

    # Если указан regex, он имеет приоритет над обычным поиском
    if regex:
        pattern = regex
    else:
        # Экранируем специальные символы, чтобы search_str
        # воспринимался как обычный текст, а не как regex
        escaped_search = re.escape(search_str)

        if full_word:
            # В отличие от \b, такая проверка лучше показывает намерение:
            # до и после совпадения не должно быть буквы, цифры
            # или символа подчёркивания
            pattern = rf"(?<!\w){escaped_search}(?!\w)"
        else:
            pattern = escaped_search

    # Учет регистра, если указан case_sensitive
    flags = 0 if case_sensitive else re.IGNORECASE

    # получаем мэтчи
    try:
        matches = re.finditer(pattern, text, flags)
    except re.error as error:
        raise ValueError(
            f"Некорректное регулярное выражение: {error}"
        ) from error

    results: list[str] = []

    # формируем чанки, на выход только те 10 чанков, которые идут после offset
    for match_number, match in enumerate(matches):
        if match_number < offset:
            continue

        left = max(0, match.start() - chunk_size)
        right = min(len(text), match.end() + chunk_size)

        snippet = text[left:right].replace("\n", " ")
        results.append(snippet)

        if len(results) == 10:
            break

    return results
