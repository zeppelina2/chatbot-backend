import re
from pathlib import Path


MAX_CHUNK_SIZE = 5000
MAX_RESULTS = 10
# границы конца предложения
SENTENCE_ENDINGS = (".", "!", "?", "\n", "...", "…")

def expand_chunk_to_sentence_boundaries(
    text: str,
    left: int,
    right: int,
    previous_chunk_end: int,
) -> tuple[int, int]:
    # Расширяет чанк до ближайшей границы предложения.

    # Слева ищет предыдущие:
    # - точку, многоточие;
    # - восклицательный и вопросительный знаки;
    # - перенос строки.

    # Справа ищет следующие такие же символы.

    # Ищем ближайший разделитель перед левой границей.
    previous_endings = [
        text.rfind(ending, previous_chunk_end, left + 1)
        for ending in SENTENCE_ENDINGS
    ]

    nearest_previous_ending = max(previous_endings)

    if nearest_previous_ending != -1:
        expanded_left = nearest_previous_ending + 1
    else:
        expanded_left = previous_chunk_end

    # Новый чанк не должен пересекаться с предыдущим.
    expanded_left = max(
        expanded_left,
        previous_chunk_end,
    )

    # Ищем ближайший разделитель после правой границы.
    next_endings = [
        position
        for ending in SENTENCE_ENDINGS
        if (position := text.find(ending, right)) != -1
    ]

    if next_endings:
        expanded_right = min(next_endings) + 1
    else:
        expanded_right = len(text)

    return expanded_left, expanded_right


def markdown_search_text(
    search_str: str,
    case_sensitive: bool = False,
    full_word: bool = False,
    regex: str = "",
    offset: int = 0,
) -> list[str]:
    f"""
    Ищет текст в Markdown-файле и возвращает не более {MAX_RESULTS} непересекающихся чанков.

    В строке поиска имеет смысл использовать stemming.
    Границы чанка расширяются до полного предложения или строки.

    Режимы поиска:
    - По умолчанию ищет полное вхождение search_str в текст.
    - При full_word=True ищет search_str как отдельное слово.
    - Если передан regex, поиск выполняется по регулярному выражению,
      а search_str и full_word игнорируются.
    - При case_sensitive=True учитывает регистр.

    Пагинация:
    - offset — количество найденных совпадений, которые нужно пропустить.
    - Возвращается не более {MAX_RESULTS} совпадений после offset.

    Размер чанка:
    - {MAX_CHUNK_SIZE} символов до совпадения;
    - найденный текст;
    - {MAX_CHUNK_SIZE} символов после совпадения;
    """

    md_path = Path("app/resources/ecumene.md")
    
    results: list[str] = []

    # Проверяем крайние случаи:
    if not md_path.is_file():
        return []

    chunk_size = MAX_CHUNK_SIZE

    if offset < 0:
        results.append(
            "offset не может быть отрицательным."
            "В следующий раз используй offset больше или равный нулю"
        )

    if not regex and not search_str:
        results.append(
            "Исправь регулярное выражение и повтори вызов "
            "markdown_search_text. Если regex не нужен, "
            "повтори вызов markdown_search_text со строкой поиска search_str."
        )
        return results

    # print("results with error: ", results)

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
        compiled_pattern = re.compile(pattern, flags)
    except re.error as error:
        raise ValueError(
            f"Некорректное регулярное выражение: {error}"
        ) from error

    text = md_path.read_text(encoding="utf-8")
    matches = compiled_pattern.finditer(text)

    # граница предыдущего чанка
    previous_chunk_end = 0
    # число посчитанных чанков
    chunk_number = 0

    # формируем чанки, на выход только те 10 чанков, которые идут после offset
    for match in matches:
        # Вхождение уже находится внутри предыдущего чанка.
        if match.start() < previous_chunk_end:
            continue

        # Сначала формируем приблизительные границы чанка.
        left = max(
            previous_chunk_end,
            match.start() - chunk_size,
        )
        right = min(
            len(text),
            match.end() + chunk_size,
        )

        # Затем расширяем их до границ предложений.
        left, right = expand_chunk_to_sentence_boundaries(
            text=text,
            left=left,
            right=right,
            previous_chunk_end=previous_chunk_end,
        )

        if left >= right:
            continue

        # Запоминаем границу до обработки offset,
        # чтобы пагинация также не создавала пересечений.
        previous_chunk_end = right

        if chunk_number < offset:
            chunk_number += 1
            continue

        snippet = re.sub(
            r"\s+",
            " ",
            text[left:right],
        ).strip()
        
        # print("snippet: ", snippet)
        # print("\n")

        results.append(snippet)
        chunk_number += 1

        if len(results) == MAX_RESULTS:
            break

    return results
