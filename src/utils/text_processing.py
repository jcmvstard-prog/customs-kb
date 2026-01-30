"""
Text processing utilities for chunking and cleaning.
"""
import re
from typing import List
from bs4 import BeautifulSoup


def strip_html(html_text: str) -> str:
    """
    Remove HTML tags and clean text.

    Args:
        html_text: HTML content

    Returns:
        str: Cleaned text
    """
    if not html_text:
        return ""

    soup = BeautifulSoup(html_text, 'lxml')
    text = soup.get_text(separator=' ', strip=True)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Maximum tokens per chunk (approximate using words)
        overlap: Number of overlapping tokens between chunks

    Returns:
        List[str]: List of text chunks
    """
    if not text:
        return []

    # Simple word-based chunking (approximation of tokens)
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(' '.join(chunk_words))

        # Move start forward with overlap
        start = end - overlap

        # Avoid infinite loop
        if start >= len(words):
            break

    return chunks


def extract_hts_codes(text: str) -> List[str]:
    """
    Extract HTS codes from text using regex.

    HTS codes follow pattern: XXXX.XX.XX (4 digits, 2 digits, 2 digits)

    Args:
        text: Text to search

    Returns:
        List[str]: List of found HTS codes
    """
    if not text:
        return []

    # Pattern: 4 digits, dot, 2 digits, dot, 2 digits
    pattern = r'\b\d{4}\.\d{2}\.\d{2}\b'
    codes = re.findall(pattern, text)

    # Remove duplicates and return
    return list(set(codes))


def normalize_text(text: str) -> str:
    """
    Normalize text for better embedding quality.

    Args:
        text: Raw text

    Returns:
        str: Normalized text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep sentence structure
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)

    return text.strip()
