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
        # Resolve absolute path to vector store
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Path: src/rag/ -> ../../vector_store/data/chroma
        persist_dir = os.path.abspath(os.path.join(current_dir, "../../vector_store/data/chroma"))
        
        self.skill_search = SkillSearchService(persist_dir=persist_dir)
        self.graph = Neo4jConnection()
        self.active_skills = self._get_active_skills()
        print(f"   [RAG] Loaded {len(self.active_skills)} active skills (skills with VR Apps)")

    def _get_active_skills(self) -> List[str]:
        """Fetch all skills that are actually connected to VR Apps."""
        try:
            cypher = """
            MATCH (s:Skill)<-[:DEVELOPS]-(a:VRApp)
            RETURN DISTINCT s.name as skill
            """
            result = self.graph.query(cypher)
            return [r["skill"] for r in result]
        except Exception as e:
            print(f"   [RAG] Warning: Failed to load active skills: {e}")
            return []

    def retrieve(self, query: str, top_k: int = 8) -> List[Dict]:
        """
        Main retrieval function.
        Implements Hybrid Retrieval with Semantic Bridging:
        1. Direct Skill Search: Query -> Skill -> VRApp
        2. Semantic Bridge: Query -> (Similarity) -> Active Skill -> VRApp
           (Used when direct search fails or returns few results)

        Args:
            query: User query string
            top_k: Number of applications to retrieve

        Returns:
            List of dictionaries containing VR application data
        """
        # Auto-refresh active skills if empty (handles case where graph was built after startup)
        if not self.active_skills:
            print("   [RAG] Active skills cache is empty. Refreshing from graph...")
            self.active_skills = self._get_active_skills()
            print(f"   [RAG] Refreshed: {len(self.active_skills)} active skills loaded")

        candidates = {}
        
        # Thresholds
        BRIDGE_SIMILARITY_THRESHOLD = 0.35  # Minimum similarity to bridge (0-1)
        
        # --- Strategy 1: Direct Skill Retrieval ---
        # Vector search for related skills -> Apps
        # We get more candidates initially to filter
        related_skills = self.skill_search.find_related_skills(query, top_k=10)
        
        if related_skills:
            direct_apps = self._query_apps_by_skills(related_skills, top_k)
            for app in direct_apps:
                app["retrieval_source"] = "direct_skill_match"
                candidates[app["name"]] = app

        # --- Strategy 2: Semantic Bridge Retrieval (The "Missing Link" Fix) ---
        # If we have few results, try to bridge from the query to known active skills
        if len(candidates) < 3:
            print(f"   [RAG] Low direct matches ({len(candidates)}). Attempting Semantic Bridge...")
            
            # Find which Active Skills are closest to the query
            bridged_skills_data = self.skill_search.find_nearest_from_candidates(
                query, 
                self.active_skills, 
                top_k=5, 
                min_similarity=BRIDGE_SIMILARITY_THRESHOLD
            )
            
            if bridged_skills_data:
                # Extract names and scores
                bridge_map = {item["name"]: item["score"] for item in bridged_skills_data}
                bridge_names = list(bridge_map.keys())
                
                # Query apps for these bridged skills
                bridged_apps = self._query_apps_by_skills(bridge_names, top_k)
                
                for app in bridged_apps:
                    # Only add if not already present
                    if app["name"] not in candidates:
                        # Find which skill caused this app to be found
                        # The app result contains 'matched_skills'. We pick the best one from our bridge list.
                        caused_by = []
                        best_bridge_score = 0
                        best_bridge_skill = None
                        
                        for s in app.get("matched_skills", []):
                            if s in bridge_map:
                                score = bridge_map[s]
                                caused_by.append(f"{s} ({score*100:.0f}%)")
                                if score > best_bridge_score:
                                    best_bridge_score = score
                                    best_bridge_skill = s
                        
                        if best_bridge_skill:
                            app["retrieval_source"] = "semantic_bridge"
                            app["bridge_explanation"] = f"Related to '{best_bridge_skill}'"
                            # Penalize score slightly based on bridge distance
                            # Original score is sum of weights. We multiply by similarity.
                            app["score"] = app["score"] * best_bridge_score
                            candidates[app["name"]] = app

        # Convert dict back to list and sort by score
        final_results = list(candidates.values())
        final_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return final_results[:top_k]

    def _query_apps_by_course(self, query_text: str, top_k: int) -> List[Dict]:
        """
        Query Neo4j for VR apps recommended for a specific course.
        Matches course_id (exact/regex) or title (fuzzy).
        """
        import re
        
        clean_query = query_text.strip()
        
        # 1. Try to find a CMU course ID (e.g., 15-112, 95-729)
        # Matches XX-XXX format
        course_id_match = re.search(r'\b(\d{2}-\d{3})\b', clean_query)
        
        if course_id_match:
            course_id = course_id_match.group(1)
            print(f"   [Course Search] Detected Course ID: {course_id}")
            
            cypher = """
            MATCH (c:Course {course_id: $course_id})
            MATCH (c)-[r:RECOMMENDS]->(a:VRApp)
            RETURN a.app_id AS app_id,
                   a.name AS name,
                   a.category AS category,
                   a.description AS description,
                   r.shared_skills AS matched_skills,
                   r.score AS score
            ORDER BY r.score DESC
            LIMIT $top_k
            """
            return self.graph.query(cypher, {"course_id": course_id, "top_k": top_k})

        # 2. Fallback: Title contains search
        # Only perform if the query is short enough to be a title, or risk false positives?
        # For now, we stick to the simple CONTAINS but maybe boost matches
        
        cypher = """
        MATCH (c:Course)
        WHERE toLower(c.title) CONTAINS toLower($query)
        MATCH (c)-[r:RECOMMENDS]->(a:VRApp)
        RETURN a.app_id AS app_id,
               a.name AS name,
               a.category AS category,
               a.description AS description,
               r.shared_skills AS matched_skills,
               r.score AS score
            ORDER BY r.score DESC
            LIMIT $top_k
        """

        results = self.graph.query(cypher, {
            "query": clean_query,
            "top_k": top_k
        })
        
        return results

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
