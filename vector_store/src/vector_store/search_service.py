"""
High-level search service for skill vector operations.

Provides a simple interface for RAG systems and other components
to search and retrieve skills using semantic similarity.
"""

from typing import List, Dict, Optional
from .indexer import VectorIndexer


class SkillSearchService:
    """
    Search service for skill semantic search.

    This service is designed to be used by RAG systems and other
    components that need to find related skills.
    """

    def __init__(
        self,
        persist_dir: str = "vector_store/data/chroma",
        use_openai: bool = False,
        model_name: str = None
    ):
        """
        Initialize the search service.

        Args:
            persist_dir: ChromaDB persistence directory
            use_openai: If True, use OpenAI embeddings
            model_name: Specific model name
        """
        self.indexer = VectorIndexer(
            use_openai=use_openai,
            persist_dir=persist_dir,
            model_name=model_name
        )

    def find_related_skills(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.3,
        category_filter: Optional[str] = None
    ) -> List[str]:
        """
        Find skills related to a query.

        Args:
            query: Search query text
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0.0-1.0)
            category_filter: Optional category to filter results

        Returns:
            List of skill names
        """
        results = self.indexer.search(
            query=query,
            top_k=top_k * 2,  # Get more to allow filtering
            min_similarity=min_similarity
        )

        # Filter by category if specified
        if category_filter:
            results = [
                (name, score, meta)
                for name, score, meta in results
                if meta.get("category") == category_filter
            ]

        # Extract names
        skills = [name for name, _, _ in results[:top_k]]

        return skills

    def find_skills_with_scores(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict]:
        """
        Find skills with their similarity scores.

        Args:
            query: Search query text
            top_k: Number of results
            min_similarity: Minimum similarity

        Returns:
            List of dicts: [{"name": "...", "score": ..., "category": ...}, ...]
        """
        results = self.indexer.search(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )

        return [
            {
                "name": name,
                "score": score,
                "category": meta.get("category", "unknown"),
                "aliases": meta.get("aliases", "").split(","),
                "source_count": meta.get("source_count", 0),
                "weight": meta.get("weight", 0.0)
            }
            for name, score, meta in results
        ]

    def find_skills_by_category(
        self,
        category: str,
        top_k: int = 20
    ) -> List[str]:
        """
        Find all skills in a specific category.

        Args:
            category: Category name (technical, soft, domain)
            top_k: Maximum number of results

        Returns:
            List of skill names in the category
        """
        # Use a generic query and filter
        results = self.find_skills_with_scores(
            query=category,
            top_k=100,
            min_similarity=0.0
        )

        # Filter to exact category match
        category_skills = [
            item["name"]
            for item in results
            if item["category"] == category
        ][:top_k]

        return category_skills

    def find_skills_by_text(
        self,
        text: str,
        min_similarity: float = 0.5
    ) -> List[str]:
        """
        Find skills that match text (exact or similar).

        Args:
            text: Text to match
            min_similarity: Minimum similarity threshold

        Returns:
            List of matching skill names
        """
        results = self.indexer.search(
            query=text,
            top_k=50,
            min_similarity=min_similarity
        )

        return [name for name, _, _ in results]

    def get_skill_recommendations(
        self,
        query: str,
        num_recommendations: int = 5
    ) -> List[Dict]:
        """
        Get diverse skill recommendations for a query.

        Ensures recommendations span different categories.

        Args:
            query: Search query
            num_recommendations: Number of recommendations

        Returns:
            List of recommended skills with metadata
        """
        all_results = self.indexer.search(
            query=query,
            top_k=num_recommendations * 3,  # Get more to diversify
            min_similarity=0.3
        )

        # Group by category
        by_category = {}
        for name, score, meta in all_results:
            category = meta.get("category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((name, score, meta))

        # Select top from each category
        recommendations = []
        categories = sorted(by_category.keys())

        for category in categories:
            if len(recommendations) >= num_recommendations:
                break
            # Take best from this category
            category_items = by_category[category][:2]
            for item in category_items:
                if len(recommendations) >= num_recommendations:
                    break
                name, score, meta = item
                recommendations.append({
                    "name": name,
                    "score": score,
                    "category": category,
                    "weight": meta.get("weight", 0.0)
                })

        return recommendations[:num_recommendations]

    def search_multiple_queries(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> Dict[str, List[str]]:
        """
        Search multiple queries and return grouped results.

        Args:
            queries: List of query strings
            top_k: Results per query

        Returns:
            Dict mapping query to list of skill names
        """
        results = self.indexer.batch_search(queries, top_k)

        return {
            query: [name for name, _, _ in result_list]
            for query, result_list in zip(queries, results)
        }

    def get_stats(self) -> Dict:
        """Get service statistics."""
        return self.indexer.get_stats()
