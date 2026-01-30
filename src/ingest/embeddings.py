"""
Text embedding generation using sentence-transformers.
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm

from src.config.settings import settings
from src.utils.logging_config import get_logger
from src.utils.text_processing import chunk_text, normalize_text

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text chunks."""

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding generator.

        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name or settings.embedding_model
        self.model: Optional[SentenceTransformer] = None
        self.batch_size = settings.batch_size

    def load_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            np.ndarray: Embedding vector
        """
        self.load_model()
        normalized = normalize_text(text)
        embedding = self.model.encode(normalized, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: List[str], show_progress: bool = False) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar

        Returns:
            List[np.ndarray]: List of embedding vectors
        """
        self.load_model()

        # Normalize texts
        normalized_texts = [normalize_text(text) for text in texts]

        # Generate embeddings in batches
        embeddings = []
        iterator = range(0, len(normalized_texts), self.batch_size)

        if show_progress:
            iterator = tqdm(iterator, desc="Generating embeddings")

        for i in iterator:
            batch = normalized_texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)

        return embeddings

    def chunk_and_embed(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[tuple[str, np.ndarray]]:
        """
        Chunk text and generate embeddings for each chunk.

        Args:
            text: Text to process
            chunk_size: Maximum tokens per chunk
            overlap: Overlap between chunks

        Returns:
            List[tuple[str, np.ndarray]]: List of (chunk_text, embedding) tuples
        """
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap

        # Chunk text
        chunks = chunk_text(text, chunk_size, overlap)

        if not chunks:
            return []

        # Generate embeddings
        embeddings = self.embed_batch(chunks)

        return list(zip(chunks, embeddings))


# Global instance
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """
    Get global embedding generator instance.

    Returns:
        EmbeddingGenerator: Embedding generator
    """
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator
