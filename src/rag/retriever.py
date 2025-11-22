"""RAG retriever component for VR app recommendations.

This module provides the retrieval pipeline that combines vector search
with knowledge graph queries to find relevant VR applications.
"""

from typing import List, Dict
import sys
import os

# Add knowledge_graph and vector_store to path for imports
kg_path = os.path.join(os.path.dirname(__file__), "../../knowledge_graph/src")
vs_path = os.path.join(os.path.dirname(__file__), "../../vector_store/src")

if kg_path not in sys.path:
    sys.path.append(kg_path)
if vs_path not in sys.path:
    sys.path.append(vs_path)

from vector_store.search_service import SkillSearchService
from knowledge_graph.connection import Neo4jConnection


class RAGRetriever:
    """Retrieves VR applications by combining vector search and graph queries."""

    def __init__(self):
        """Initialize the retriever with search and graph services."""
        self.skill_search = SkillSearchService()
        self.graph = Neo4jConnection()

    def retrieve(self, query: str, top_k: int = 8) -> List[Dict]:
        """
        Main retrieval function.

        Args:
            query: User query string
            top_k: Number of applications to retrieve

        Returns:
            List of dictionaries containing VR application data
        """
        # 1. Vector search for related skills
        related_skills = self.skill_search.find_related_skills(query, top_k=15)

        if not related_skills:
            return []

        # 2. Query knowledge graph for related applications
        apps = self._query_apps_by_skills(related_skills, top_k)

        return apps

    def _query_apps_by_skills(self, skills: List[str], top_k: int) -> List[Dict]:
        """
        Query Neo4j knowledge graph for VR applications based on skills.

        Args:
            skills: List of skill names
            top_k: Maximum number of results

        Returns:
            List of VR application dictionaries
        """
        cypher = """
        MATCH (s:Skill)<-[d:DEVELOPS]-(a:VRApp)
        WHERE s.name IN $skills
        WITH a, collect(s.name) AS matched_skills, sum(d.weight) AS score
        RETURN a.app_id AS app_id,
               a.name AS name,
               a.category AS category,
               a.description AS description,
               matched_skills,
               score
        ORDER BY score DESC, size(matched_skills) DESC
        LIMIT $top_k
        """

        results = self.graph.query(cypher, {
            "skills": skills,
            "top_k": top_k
        })

        return results

    def close(self):
        """Close connections to services."""
        self.graph.close()
