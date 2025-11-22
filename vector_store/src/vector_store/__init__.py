"""
Stage 4: Vector Store & Embeddings Module

This module provides semantic search capabilities for skills using
vector embeddings and ChromaDB.
"""

from .embeddings import (
    EmbeddingModel,
    LocalEmbedding,
    OpenAIEmbedding,
    get_embedding_model
)

from .indexer import VectorIndexer
from .search_service import SkillSearchService

__all__ = [
    'EmbeddingModel',
    'LocalEmbedding',
    'OpenAIEmbedding',
    'get_embedding_model',
    'VectorIndexer',
    'SkillSearchService'
]
