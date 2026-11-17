import pytest

from app.services.chunking import chunk_text


def test_short_text_is_a_single_chunk():
    assert chunk_text("Hello world.", chunk_size=100, overlap=20) == ["Hello world."]


def test_empty_text_gives_no_chunks():
    assert chunk_text("   \n\n  ", chunk_size=100, overlap=20) == []


def test_small_paragraphs_are_packed_together():
    text = "First para.\n\nSecond para.\n\nThird para."
    assert chunk_text(text, chunk_size=100, overlap=20) == ["First para.\n\nSecond para.\n\nThird para."]


def test_chunks_respect_soft_size_limit_and_keep_every_paragraph():
    paragraphs = [f"Paragraph number {i} talks about topic {i} in some detail." for i in range(20)]
    chunks = chunk_text("\n\n".join(paragraphs), chunk_size=200, overlap=40)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 200 + 40 + 2
    for p in paragraphs:
        assert any(p in c for c in chunks)


def test_consecutive_chunks_overlap():
    paragraphs = [f"Paragraph number {i} talks about topic {i} in some detail." for i in range(20)]
    chunks = chunk_text("\n\n".join(paragraphs), chunk_size=200, overlap=40)

    for prev, nxt in zip(chunks, chunks[1:]):
        last_word = prev.split()[-1]
        assert last_word in nxt


def test_long_paragraph_is_split_on_sentences():
    sentence = "This sentence is exactly about fifty characters ok."
    paragraph = " ".join([sentence] * 10)  # ~520 chars, no blank lines
    chunks = chunk_text(paragraph, chunk_size=200, overlap=30)

    assert len(chunks) >= 3
    assert all(c.endswith(".") for c in chunks)


def test_giant_unbroken_string_is_hard_sliced():
    chunks = chunk_text("x" * 1000, chunk_size=300, overlap=50)
    assert len(chunks) >= 4


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=100)
