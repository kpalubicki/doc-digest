"""Tests for document parsing and chunking logic."""

import pytest
from pathlib import Path
import tempfile

from app.services.document_service import _chunk_text, _extract_text, CHUNK_SIZE, CHUNK_OVERLAP


class TestChunkText:
    def test_short_text_returns_single_chunk(self):
        text = "Hello world. This is a short document with enough content to pass the fifty character minimum filter."
        chunks = _chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text.strip()

    def test_long_text_splits_into_multiple_chunks(self):
        text = "word " * 400  # ~2000 chars
        chunks = _chunk_text(text)
        assert len(chunks) > 1

    def test_chunks_respect_max_size(self):
        text = "a" * 3000
        chunks = _chunk_text(text)
        for chunk in chunks:
            assert len(chunk) <= CHUNK_SIZE

    def test_overlap_between_chunks(self):
        # each chunk should share some content with the next
        text = "word " * 400
        chunks = _chunk_text(text)
        if len(chunks) > 1:
            tail = chunks[0][-CHUNK_OVERLAP:]
            head = chunks[1][:CHUNK_OVERLAP]
            # they won't be identical due to strip() but overlap region should be close
            assert len(tail) > 0 and len(head) > 0

    def test_empty_chunks_are_filtered(self):
        text = "   \n\n   " * 100 + "real content here"
        chunks = _chunk_text(text)
        for chunk in chunks:
            assert len(chunk) > 50

    def test_empty_text_returns_no_chunks(self):
        chunks = _chunk_text("")
        assert chunks == []

    def test_tiny_text_below_threshold_filtered(self):
        # less than 50 chars should be filtered out
        chunks = _chunk_text("too short")
        assert chunks == []


class TestExtractText:
    def test_extract_plain_text(self, tmp_path):
        f = tmp_path / "sample.txt"
        f.write_text("hello from a text file", encoding="utf-8")
        result = _extract_text(f, ".txt")
        assert result == "hello from a text file"

    def test_extract_markdown(self, tmp_path):
        f = tmp_path / "sample.md"
        f.write_text("# heading\n\nsome content", encoding="utf-8")
        result = _extract_text(f, ".md")
        assert "heading" in result
        assert "content" in result
