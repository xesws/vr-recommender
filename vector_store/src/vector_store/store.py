"""
ChromaDB vector store implementation for skill embeddings.

Provides persistent storage and retrieval of skill embeddings with
semantic search capabilities.
"""

import chromadb
from typing import List, Tuple, Optional
import json
import os


class SkillVectorStore:
    """ChromaDB-based vector store for skills."""

    def __init__(self, persist_dir: str = "vector_store/data/chroma"):
        """
        Initialize the vector store.

        Args:
            persist_dir: Directory for persistent storage
        """
        self.persist_dir = persist_dir
        # Ensure directory exists
        os.makedirs(persist_dir, exist_ok=True)

        # Use new ChromaDB client API
        self.client = chromadb.PersistentClient(path=persist_dir)

        self.collection = self.client.get_or_create_collection(
            name="skills",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✓ Vector store initialized at {persist_dir}")

    def add_skills(
        self,
        skills: List[dict],
        embeddings: List[List[float]]
    ):
        """
        Add skills with their embeddings to the store.

        Args:
            skills: List of skill dictionaries with 'name', 'category', 'aliases'
            embeddings: List of embedding vectors corresponding to skills
        """
        if not skills or not embeddings:
            print("⚠ Warning: No skills or embeddings provided")
            return

        ids = [s["name"] for s in skills]
        documents = [self._skill_to_document(s) for s in skills]
        metadatas = [
            {
                "category": s.get("category", "unknown"),
                "aliases": ",".join(s.get("aliases", [])),
                "source_count": s.get("source_count", 0),
                "weight": s.get("weight", 0.0)
            }
            for s in skills
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(f"✓ Added {len(skills)} skills to vector store")

    def _skill_to_document(self, skill: dict) -> str:
        """
        Convert skill to document text for embedding.

        Args:
            skill: Skill dictionary

        Returns:
            Document text representation
        """
        aliases = skill.get("aliases", [])
        alias_str = f". Also known as: {', '.join(aliases)}" if aliases else ""
        category = skill.get("category", "unknown")
        return f"{skill['name']}{alias_str}. Category: {category}"

    def search(
        self,
        query_embedding: List[float],
        query_text: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[str, float, dict]]:
        """
        Search for similar skills using embedding similarity.

        Args:
            query_embedding: Query embedding vector
            query_text: Optional query text for logging
            top_k: Number of results to return

        Returns:
            List of (skill_name, similarity_score, metadata) tuples
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["distances", "metadatas"]
        )

        skills = []
        for i, skill_id in enumerate(results["ids"][0]):
            # ChromaDB returns cosine distance (0 = identical, 2 = opposite)
            distance = results["distances"][0][i]
            similarity = 1 - distance  # Convert to similarity score

            metadata = results["metadatas"][0][i] if results["metadatas"][0] else {}

            skills.append((skill_id, similarity, metadata))

        if query_text:
            print(f"🔍 Search for '{query_text}':")
            for name, score, _ in skills[:top_k]:
                print(f"   • {name}: {score:.3f}")

        return skills

    def search_by_text(
        self,
        texts: List[str],
        embeddings_model,
        top_k: int = 10
    ) -> List[List[Tuple[str, float, dict]]]:
        """
        Search for similar skills given text queries.

        Args:
            texts: List of query texts
            embeddings_model: EmbeddingModel to encode texts
            top_k: Number of results per query

        Returns:
            List of result lists (one per query)
        """
        query_embeddings = embeddings_model.encode(texts)

        all_results = []
        for text, embedding in zip(texts, query_embeddings):
            results = self.search(
                query_embedding=embedding.tolist(),
                query_text=text,
                top_k=top_k
            )
            all_results.append(results)

        return all_results

    def get_all_skills(self) -> List[str]:
        """Get all skill names in the store."""
        try:
            result = self.collection.get(ids=None)
            return result.get("ids", [])
        except Exception:
            return []

    def get_stats(self) -> dict:
        """Get statistics about the vector store."""
        try:
            count = self.collection.count()
            return {
                "total_skills": count,
                "persist_directory": self.persist_dir
            }
        except Exception as e:
            return {"error": str(e)}

    def persist(self):
        """Persist the vector store to disk."""
        # With PersistentClient, data is automatically persisted
        print(f"✓ Vector store is persistent at {self.persist_dir}")

    def clear(self):
        """Clear all skills from the store."""
        try:
            self.client.delete_collection("skills")
            print("✓ Cleared all skills from vector store")
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name="skills",
            metadata={"hnsw:space": "cosine"}
        )

    def save_stats(self, filepath: str):
        """Save statistics to a JSON file."""
        stats = self.get_stats()
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Stats saved to {filepath}")
