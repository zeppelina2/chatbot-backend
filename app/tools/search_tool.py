from pathlib import Path

# простой поиск в файле. ищем вхождения searchStr
# и возвращаем массив срезов (100 символов до + searchStr + 100 символов после)
def markdown_search_tool(searchStr: str) -> list[str]:
    MD_PATH = Path("/resources/ecumene.md")

    if not MD_PATH.exists():
        return []

    text = MD_PATH.read_text(encoding="utf-8")
    # список сниппетов, включающих искомую строку searchStr
    results = []

    search_len = len(searchStr)
    # индекс начала сниппета в документе
    start = 0

    # делаем поиск регистронезависимым
    text_lower = text.casefold()
    search_lower = searchStr.casefold()

    while True:
        index = text_lower.find(search_lower, start)

        if index == -1:
            break

        # границы с учетом начала и конца файла
        left = max(0, index - 100)
        right = min(len(text), index + search_len + 100)

        snippet = text[left:right].replace("\n", " ")
        results.append(snippet)

        start = index + search_len  # двигаемся дальше

    return results
