"""Split text into overlapping chunks for embedding.

Strategy (structure first, size second):
  1. Split on blank lines -> paragraphs. Paragraphs are the natural unit of
     meaning in both notes and web pages, so we try hard not to cut them.
  2. A paragraph longer than `chunk_size` is split on sentence boundaries;
     a single giant "sentence" (e.g. a minified blob) is hard-sliced.
  3. Pieces are packed greedily into chunks of up to `chunk_size` chars.
  4. Each new chunk starts with the last ~`overlap` chars of the previous one,
     so a fact that straddles a boundary is still retrievable from either side.

Sizes are in characters, not tokens: no tokenizer dependency, and for English
~4 chars/token is close enough. `chunk_size` is a soft limit -- a chunk can be
up to chunk_size + overlap long because of the carried-over tail.
"""

import re

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    pieces: list[str] = []
    for paragraph in _PARAGRAPH_BREAK.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= chunk_size:
            pieces.append(paragraph)
        else:
            pieces.extend(_split_long_paragraph(paragraph, chunk_size))

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + 2 + len(piece) <= chunk_size:
            current = f"{current}\n\n{piece}"
        else:
            chunks.append(current)
            current = f"{_tail(current, overlap)}\n\n{piece}"
    if current:
        chunks.append(current)

    return chunks


def _split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(paragraph):
        if len(sentence) > chunk_size:
            if current:
                parts.append(current)
                current = ""
            parts.extend(sentence[i : i + chunk_size] for i in range(0, len(sentence), chunk_size))
        elif not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= chunk_size:
            current = f"{current} {sentence}"
        else:
            parts.append(current)
            current = sentence
    if current:
        parts.append(current)
    return parts


def _tail(text: str, size: int) -> str:
    """Last `size` chars of text, starting at a word boundary when possible."""
    if len(text) <= size:
        return text
    tail = text[-size:]
    first_space = tail.find(" ")
    return tail[first_space + 1 :] if first_space != -1 else tail
