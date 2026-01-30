"""
Tests for text processing utilities.
"""
import pytest
from src.utils.text_processing import (
    strip_html,
    chunk_text,
    extract_hts_codes,
    normalize_text
)


def test_strip_html():
    """Test HTML stripping."""
    html = "<p>This is <b>bold</b> text.</p>"
    result = strip_html(html)
    assert result == "This is bold text."


def test_strip_html_empty():
    """Test stripping empty HTML."""
    assert strip_html("") == ""
    assert strip_html(None) == ""


def test_chunk_text():
    """Test text chunking."""
    text = " ".join(["word"] * 1000)
    chunks = chunk_text(text, chunk_size=100, overlap=10)

    assert len(chunks) > 1
    assert all(len(chunk.split()) <= 100 for chunk in chunks)


def test_chunk_text_short():
    """Test chunking short text."""
    text = "Short text"
    chunks = chunk_text(text, chunk_size=100, overlap=10)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_extract_hts_codes():
    """Test HTS code extraction."""
    text = "Import duties for HTS 0406.10.00 and 0406.30.00 are listed."
    codes = extract_hts_codes(text)

    assert len(codes) == 2
    assert "0406.10.00" in codes
    assert "0406.30.00" in codes


def test_extract_hts_codes_none():
    """Test extraction with no HTS codes."""
    text = "No codes here"
    codes = extract_hts_codes(text)

    assert len(codes) == 0


def test_normalize_text():
    """Test text normalization."""
    text = "  Multiple   spaces   and\n\nnewlines  "
    result = normalize_text(text)

    assert "  " not in result
    assert result.startswith("Multiple")
    assert result.endswith("newlines")
