"""
Embedding model implementations for generating skill embeddings.

Supports both local (sentence-transformers) and OpenAI embeddings.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional
import os


class EmbeddingModel:
    """Abstract base class for embedding models."""

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of texts to embeddings.

        Args:
            texts: List of text strings to encode

        Returns:
            numpy array of embeddings (shape: len(texts) x embedding_dim)
        """
        raise NotImplementedError


class LocalEmbedding(EmbeddingModel):
    """Local embedding model using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding model.

        Args:
            model_name: sentence-transformers model name
        """
        print(f"Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("✓ Model loaded successfully")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts using local sentence-transformers model.

        Args:
            texts: List of texts to encode

        Returns:
            numpy array of embeddings
        """
        return self.model.encode(texts, show_progress_bar=True)


class OpenAIEmbedding(EmbeddingModel):
    """OpenAI embedding API wrapper."""

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding client.

        Args:
            model: OpenAI embedding model name
        """
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY or OPENROUTER_API_KEY environment variable must be set"
            )

        base_url = os.getenv("OPENAI_BASE_URL") or "https://openrouter.ai/api/v1"

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        print(f"Using OpenAI embedding model: {model}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts using OpenAI API.

        Args:
            texts: List of texts to encode

        Returns:
            numpy array of embeddings
        """
        from openai import APIError

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            embeddings = [e.embedding for e in response.data]
            return np.array(embeddings)
        except APIError as e:
            print(f"✗ OpenAI API error: {e}")
            raise


def get_embedding_model(
    use_openai: bool = False,
    model_name: Optional[str] = None
) -> EmbeddingModel:
    """
    Get an embedding model based on configuration.

    Args:
        use_openai: If True, use OpenAI embeddings; otherwise use local
        model_name: Optional model name (defaults based on provider)

    Returns:
        EmbeddingModel instance
    """
    if use_openai:
        return OpenAIEmbedding(
            model=model_name or "text-embedding-3-small"
        )
    else:
        return LocalEmbedding(
            model_name=model_name or "all-MiniLM-L6-v2"
        )
