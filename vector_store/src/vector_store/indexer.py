"""
Vector indexing pipeline for building and managing skill embeddings.

Orchestrates the process of loading skills, generating embeddings,
and storing them in ChromaDB.
"""

import json
import os
from typing import List, Tuple
from .embeddings import get_embedding_model
from .store import SkillVectorStore


class VectorIndexer:
    """Builds and manages the skill vector index."""

    def __init__(
        self,
        use_openai: bool = False,
        persist_dir: str = "vector_store/data/chroma",
        model_name: str = None
    ):
        """
        Initialize the vector indexer.

        Args:
            use_openai: If True, use OpenAI embeddings; otherwise use local
            persist_dir: Directory for ChromaDB persistence
            model_name: Specific model name to use
        """
        self.embedding_model = get_embedding_model(use_openai, model_name)
        self.store = SkillVectorStore(persist_dir)
        print(f"✓ Vector indexer initialized")

    def build_index(self, skills_path: str, clear_existing: bool = True):
        """
        Build the vector index from skills JSON file.

        Args:
            skills_path: Path to skills.json file
            clear_existing: If True, clear existing index before building
        """
        # Load skills
        if not os.path.exists(skills_path):
            raise FileNotFoundError(f"Skills file not found: {skills_path}")

        with open(skills_path, 'r') as f:
            skills = json.load(f)

        print(f"\n{'='*60}")
        print(f"BUILDING VECTOR INDEX")
        print(f"{'='*60}")
        print(f"Skills to process: {len(skills)}")
        print(f"Embedding model: {type(self.embedding_model).__name__}")
        print(f"Output directory: {self.store.persist_dir}")
        print(f"{'='*60}\n")

        # Clear existing if requested
        if clear_existing:
            self.store.clear()

        # Generate document texts
        print("Generating skill documents...")
        texts = [self._skill_to_text(s) for s in skills]

        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedding_model.encode(texts)

        # Store in vector database
        print("Storing in vector database...")
        self.store.add_skills(skills, embeddings.tolist())

        # Persist
        self.store.persist()

        # Show statistics
        stats = self.store.get_stats()
        vector_dims = embeddings.shape[1] if len(embeddings) > 0 else "N/A"

        print(f"\n{'='*60}")
        print(f"INDEX BUILD COMPLETE")
        print(f"{'='*60}")
        print(f"Total skills indexed: {stats['total_skills']}")
        print(f"Vector dimensions: {vector_dims}")
        print(f"Storage: {self.store.persist_dir}")
        print(f"{'='*60}\n")

    def _skill_to_text(self, skill: dict) -> str:
        """
        Convert skill to text for embedding.

        Args:
            skill: Skill dictionary

        Returns:
            Text representation
        """
        aliases = skill.get("aliases", [])
        alias_str = f". Also known as: {', '.join(aliases)}" if aliases else ""
        category = skill.get("category", "unknown")
        return f"{skill['name']}{alias_str}. Category: {category}"

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.0
    ) -> List[Tuple[str, float, dict]]:
        """
        Search for skills similar to query.

        Args:
            query: Query text
            top_k: Number of results
            min_similarity: Minimum similarity threshold

        Returns:
            List of (skill_name, similarity, metadata) tuples
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]

        # Search
        results = self.store.search(
            query_embedding=query_embedding.tolist(),
            query_text=query,
            top_k=top_k
        )

        # Filter by minimum similarity
        filtered = [(name, score, meta) for name, score, meta in results
                   if score >= min_similarity]

        return filtered

    def batch_search(
        self,
        queries: List[str],
        top_k: int = 10
    ) -> List[List[Tuple[str, float, dict]]]:
        """
        Perform batch search for multiple queries.

        Args:
            queries: List of query texts
            top_k: Number of results per query

        Returns:
            List of result lists (one per query)
        """
        return self.store.search_by_text(queries, self.embedding_model, top_k)

    def get_skill_info(self, skill_name: str) -> dict:
        """
        Get information about a specific skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill metadata or empty dict if not found
        """
        try:
            result = self.store.collection.get(ids=[skill_name])
            if result["metadatas"]:
                return result["metadatas"][0]
            return {}
        except Exception:
            return {}

    def get_stats(self) -> dict:
        """Get index statistics."""
        return self.store.get_stats()

    def update_index(
        self,
        skills_path: str,
        clear_existing: bool = False
    ):
        """
        Update the index with new skills.

        Args:
            skills_path: Path to updated skills.json
            clear_existing: If True, rebuild from scratch
        """
        print("\nUpdating vector index...")
        self.build_index(skills_path, clear_existing)
        print("✓ Index updated successfully")
