"""
RAG-Based VR App Recommender for Heinz College
----------------------------------------------
• Uses RAG (Retrieval-Augmented Generation) system combining ChromaDB and Neo4j
• Integrates vector search with knowledge graph queries
• Provides intelligent VR app recommendations with explanations

Usage
-----
export OPENROUTER_API_KEY=sk-or-v1-...
python vr_recommender.py

Integrate into your web app by importing HeinzVRLLMRecommender and calling
  generate_recommendation(StudentQuery(...))

Notes
-----
- Requires Neo4j, ChromaDB, and OpenRouter API
- Provides detailed reasoning for each recommendation
"""

from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from src.rag.service import RAGService


# ----------------------------- Data Model ----------------------------- #

@dataclass
class StudentQuery:
    query: str
    interests: List[str]
    background: str = ""


# --------------------------- Recommender ------------------------------ #

class HeinzVRLLMRecommender:
    """RAG-based recommender: Combines vector search with knowledge graph."""

    def __init__(self):
        """Initialize the RAG-based recommender."""
        self.rag_service = RAGService()

    def recommend_vr_apps(self, query: StudentQuery) -> List[Dict]:
        """
        Generate VR app recommendations using RAG system.

        Args:
            query: StudentQuery object containing user query and interests

        Returns:
            List[Dict]: Recommended VR applications with scores and reasoning
        """
        # Build full query text from StudentQuery
        full_query = query.query
        if query.interests:
            full_query += f". Interests: {', '.join(query.interests)}"

        # Call RAG service
        result = self.rag_service.recommend(full_query, top_k=8)

        # Convert to old API format for compatibility
        apps = []
        max_score = max([app.score for app in result.apps], default=1)

        for app in result.apps:
            # Calculate base normalized score (relative to best result)
            normalized_score = app.score / max_score
            
            # Apply strict confidence penalty for semantic bridges
            # Bridged results should never exceed 49% confidence to manage expectations
            if app.retrieval_source == "semantic_bridge":
                normalized_score = min(normalized_score, 0.49)
                
            apps.append({
                "app_name": app.name,
                "likeliness_score": round(min(1.0, normalized_score), 2),
                "category": app.category,
                "reasoning": app.reasoning,
                "retrieval_source": app.retrieval_source,
                "bridge_explanation": app.bridge_explanation
            })

        return apps

    def generate_recommendation(self, query: StudentQuery) -> Dict:
        """
        Generate complete recommendation response.

        Args:
            query: StudentQuery object

        Returns:
            Dict: Complete recommendation with apps and metadata
        """
        print(f"\n🔍 Processing (RAG): {query.query}")

        try:
            vr_apps = self.recommend_vr_apps(query)
            return {
                "student_query": query.query,
                "vr_apps": vr_apps,
                "message": f"Here are {len(vr_apps)} VR apps aligned to your interests.",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "student_query": query.query,
                "vr_apps": [],
                "message": f"Error: {str(e)}",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

    def close(self):
        """Close connections to RAG services."""
        self.rag_service.close()


# ------------------------------ CLI ---------------------------------- #

def main():
    print("=" * 70)
    print("HEINZ RAG VR APP RECOMMENDER")
    print("=" * 70)

    rec = HeinzVRLLMRecommender()

    demos = [
        StudentQuery("I want to learn about cyber security", ["projects"], "MSISPM"),
        StudentQuery("machine learning for public policy", ["data analysis"], "MSPPM"),
        StudentQuery("data visualization", ["tableau"], "MISM"),
    ]

    for q in demos:
        out = rec.generate_recommendation(q)
        print(f"\nQuery: {out['student_query']}")
        print("Apps:")
        for a in out["vr_apps"][:5]:
            print(f"  • {a['app_name']} — {a['category']} ({int(a['likeliness_score']*100)}%)")
            print(f"    {a['reasoning']}")

    rec.close()


if __name__ == "__main__":
    main()
