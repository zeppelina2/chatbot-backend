from pathlib import Path


def markdown_search_text(search_str: str, chunk_size: int) -> list[str]:
    """
    Полнотекстовый поиск в файле ищет по полному вхождению search_str.
    В строке поиска имеет смысл использовать stemming.
    Например, если нужно найти все про "гетайров", то search_str лучше указывать "гетайр".
    Функция возвращает массив срезов (chunk_size символов до + search_str + chunk_size символов после).
    """
    
    MD_PATH = Path("app/resources/ecumene.md")

    if not MD_PATH.exists():
        print("НЕ НАШЕЛ ПУТЬ")
        return []

    text = MD_PATH.read_text(encoding="utf-8")
    # список сниппетов, включающих искомую строку search_str
    results = []

    search_len = len(search_str)
    # индекс начала сниппета в документе
    start = 0

    # делаем поиск регистронезависимым
    text_lower = text.casefold()
    search_lower = search_str.casefold()

    while True:
        index = text_lower.find(search_lower, start)

        if index == -1:
            break

        # границы с учетом начала и конца файла
        left = max(0, index - chunk_size)
        right = min(len(text), index + search_len + chunk_size)

        snippet = text[left:right].replace("\n", " ")
        results.append(snippet)

        start = index + search_len  # двигаемся дальше

    return results
