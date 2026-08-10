import tempfile
import os
import pytest
from app.document_processing.chunker import chunk_text
from app.rag.embedder import embed_query, embed_texts
from app.document_processing.cleaner import clean_text
from app.document_processing.extractor import extract_text



def test_chunk_text_basic():
    text = " ".join(["word"] * 600)
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 2
    assert len(chunks[0].split()) == 500
    assert len(chunks[1].split()) == 150


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_chunk_text_small():
    text = "This is a small document."
    chunks = chunk_text(text, chunk_size=500)
    assert len(chunks) == 1


def test_clean_text():
    raw = "Hello   world\n\n\n\nfoo   bar"
    cleaned = clean_text(raw)
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned


def test_embed_query_dimensions():
    embedding = embed_query("What is machine learning?")
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_embed_texts_batch():
    texts = ["Hello world", "Machine learning is great"]
    embeddings = embed_texts(texts)
    assert len(embeddings) == 2
    assert all(len(e) == 384 for e in embeddings)


def test_extract_txt():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Hello from test file.")
        tmp_path = f.name
    try:
        text = extract_text(tmp_path, "txt")
        assert "Hello from test file." in text
    finally:
        os.unlink(tmp_path)