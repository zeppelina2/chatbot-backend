from __future__ import annotations
from pathlib import Path
import json
import re
from collections.abc import Iterator
from typing import TypedDict


MAX_CHUNK_SIZE = 5000


# функция сохранения чанков в json файл
def save_chunks(
    chunks: list[MarkdownChunk],
    file_path: str | Path,
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return path

"""Нарезка Markdown по каждому ATX-заголовку (# — ######).

Заголовки хранятся в path, chunk содержит только собственный текст раздела.
Пустые/пробельные разделы пропускаются. Пробелы по краям частей удаляются,
внутреннее форматирование сохраняется. Текст до первого заголовка: path=['1'].
Номер части добавляется к пути всегда. Повторяющиеся цепочки заголовков могут
давать одинаковые path; chunk_id уникален в рамках результата одной нарезки,
но не стабилен при изменении документа. part/parts считаются для каждого
отдельного вхождения раздела, а не для группы одинаковых названий.

Поддерживаются обычные Markdown-заголовки с пробелом после # и fenced code.
Setext-заголовки и полная грамматика CommonMark не поддерживаются.
Разделение предложений эвристическое (возможны разрывы после сокращений).
Большие таблицы и блоки кода могут разделяться: отдельные чанки не обязательно
являются самостоятельными корректно отображаемыми Markdown-документами.
"""

class MarkdownChunk(TypedDict):
    chunk_id: int
    path: list[str]
    part: int
    parts: int
    chunk: str


_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$") # Заголовки
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$") # Ограждения вида "```" или "~~~"
_BOUNDARIES = (
    re.compile(r"\r?\n[ \t]*\r?\n(?:[ \t]*\r?\n)*"),  # Абзацы
    re.compile(r'''[.!?…]+[»”"')\]]*\s+'''),          # Предложения
    re.compile(r"\s+"),                               # Слова
)
# Символы пунктуации, которые Markdown позволяет экранировать
MARKDOWN_ESCAPE_RE = re.compile(
    r"""\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])"""
)
# Простое парное форматирование: жирный, курсив, зачёркивание.
FORMATTING_RE = re.compile(
    r"(?<!\*)(\*{1,3})(?!\*)(?=\S)(.+?)(?<=\S)\1(?!\*)"
    r"|(?<![\w_])(_{1,3})(?!_)(?=\S)(.+?)(?<=\S)\3(?![\w_])"
    r"|(?<!~)(~~)(?!~)(?=\S)(.+?)(?<=\S)\5(?!~)"
)


def _clean_heading(title: str) -> str:
    """Убрать простую разметку, сохранив буквальные символы."""
    protected: list[str] = []

    def protect(value: str) -> str:
        protected.append(value)
        return f"\x00{len(protected) - 1}\x00"

    # Скрываем экранированные символы до очистки разметки.
    title = MARKDOWN_ESCAPE_RE.sub(
        lambda match: protect(match.group(1)),
        title,
    )

    # Сохраняем содержимое инлайн-кода без обработки его как разметки.
    title = re.sub(
        r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)",
        lambda match: protect(match.group(2)),
        title,
    )

    # Необязательные закрывающие #.
    title = re.sub(r"[ \t]+#+[ \t]*$", "", title)

    # Изображения и ссылки: сохраняем видимый текст.
    title = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", title)

    # HTML-теги.
    title = re.sub(r"</?[A-Za-z][^>]*>", "", title)

    # Удаляем парные маркеры. Повторяем для вложенного форматирования.
    while True:
        cleaned = FORMATTING_RE.sub(
            lambda match: next(
                value
                for value in (
                    match.group(2),
                    match.group(4),
                    match.group(6),
                )
                if value is not None
            ),
            title,
        )

        if cleaned == title:
            break

        title = cleaned

    # Восстанавливаем защищённый текст.
    # Обратный порядок нужен, если инлайн-код содержит другие подстановки.
    for index in range(len(protected) - 1, -1, -1):
        title = title.replace(
            f"\x00{index}\x00",
            protected[index],
        )

    return title.strip()


def _sections(text: str) -> Iterator[tuple[list[str], str]]:
    """Каждый заголовок завершает предыдущий раздел, независимо от уровня."""
    stack: list[tuple[int, str]] = []
    lines: list[str] = []
    fence_char, fence_length = "", 0

    for line in text.splitlines(keepends=True):
        value = line.rstrip("\r\n")
        fence = _FENCE.match(value)
        if fence_char:
            if (fence and fence[1][0] == fence_char
                    and len(fence[1]) >= fence_length and not fence[2].strip()):
                fence_char = ""
        elif fence and not (fence[1][0] == "`" and "`" in fence[2]):
            fence_char, fence_length = fence[1][0], len(fence[1])
        elif heading := _HEADING.match(value):
            yield [label for _, label in stack], "".join(lines)
            lines = []
            level = len(heading[1])
            title = _clean_heading(heading[2] or "")
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, f"{heading[1]}{title}"))
            continue
        lines.append(line)

    yield [label for _, label in stack], "".join(lines)


def _split_text(text: str, limit: int, depth: int = 0) -> list[str]:
    """Абзацы → предложения → слова → символы; затем упаковка до лимита."""
    if len(text) <= limit:
        return [text] if text else []
    if depth == len(_BOUNDARIES):
        return [text[i:i + limit] for i in range(0, len(text), limit)]

    pieces: list[str] = []
    start = 0
    for match in _BOUNDARIES[depth].finditer(text):
        pieces.extend(_split_text(text[start:match.end()], limit, depth + 1))
        start = match.end()
    pieces.extend(_split_text(text[start:], limit, depth + 1))

    packed: list[str] = []
    for piece in pieces:
        if packed and len(packed[-1]) + len(piece) <= limit:
            packed[-1] += piece
        else:
            packed.append(piece)
    return packed


def chunk_markdown_with_tree(
    text: str,
    document_name: str,
    max_chunk_size: int = MAX_CHUNK_SIZE,
) -> tuple[list[MarkdownChunk], str]:
    """Создать чанки и дерево заголовков документа."""
    if isinstance(max_chunk_size, bool) or not isinstance(max_chunk_size, int):
        raise TypeError("max_chunk_size должен быть целым числом")

    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size должен быть больше нуля")

    chunks: list[MarkdownChunk] = []
    tree_lines: list[str] = [document_name]

    for path, content in _sections(text):
        parts = [
            piece.strip()
            for piece in _split_text(content.strip(), max_chunk_size)
            if piece.strip()
        ]
        parts_count = len(parts)

        if path:
            heading = path[-1]

            # Количество # определяет уровень заголовка.
            level = len(heading) - len(heading.lstrip("#"))
            indent = "\t" * level

            tree_lines.append(f"{indent}{heading}")

            if parts_count > 1:
                tree_lines.append(f"{indent}\t{parts_count}")

        elif parts_count:
            # Текст до первого заголовка тоже может иметь чанки.
            tree_lines.append("\t[Текст до первого заголовка]")

            if parts_count > 1:
                tree_lines.append(f"\t\t{parts_count}")

        for part, piece in enumerate(parts, start=1):
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "path": [*path, f"часть {str(part)}"] if part > 1 else [*path],
                "part": part,
                "parts": parts_count,
                "chunk": piece,
            })

    return chunks, "\n".join(tree_lines)


# Форматирует чанки в базу знаний, где key = path, пара для него - соответствующий path чанк
def create_knowlege_library_from_markdown(
    file_paths: list[str | Path],
) -> tuple[dict[tuple[str, ...], list[MarkdownChunk]], str]:
    knowledge_library: dict[tuple[str, ...], list[MarkdownChunk]] = {}
    headings_trees: list[str] = []
    document_names: set[str] = set()
    chunk_id = 0

    for file_path in file_paths:
        path = Path(file_path)
        document_name = path.stem

        # Имя документа используется в ключах базы — оно должно быть уникальным.
        if document_name in document_names:
            raise ValueError(
                f"Повторяющееся имя документа: {document_name!r}. "
                "Используйте файлы с разными именами."
            )

        document_names.add(document_name)
        text = path.read_text(encoding="utf-8")

        chunks, headings_tree = chunk_markdown_with_tree(
            text=text,
            document_name=document_name,
        )
        
        # save_chunks(chunks, f"app/resources/{document_name}.json")

        headings_trees.append(headings_tree)

        for chunk in chunks:
            chunk_id += 1

            library_chunk: MarkdownChunk = {
                **chunk,
                "chunk_id": chunk_id,
                "path": [document_name, *chunk["path"]],
            }

            key = tuple(library_chunk["path"])
            knowledge_library.setdefault(key, []).append(library_chunk)

    return knowledge_library, "\n\n".join(headings_trees)
