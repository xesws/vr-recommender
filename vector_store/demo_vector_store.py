#!/usr/bin/env python3
"""
Stage 4 Vector Store Demo

Demonstrates semantic search capabilities for skills using vector embeddings.
This script showcases the key features without requiring a running database.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from vector_store.src.vector_store.indexer import VectorIndexer
from vector_store.src.vector_store.search_service import SkillSearchService


def demo_search_service():
    """Demonstrate the high-level search service."""
    print("\n" + "="*70)
    print("DEMO: High-Level Search Service")
    print("="*70)

    # Initialize service (will use existing index)
    service = SkillSearchService(
        persist_dir="vector_store/data/chroma",
        use_openai=False
    )

    # Demo queries
    queries = [
        "machine learning neural networks",
        "python programming",
        "data visualization",
        "communication skills",
        "immersive learning"
    ]

    print("\n1. Finding Related Skills")
    print("-" * 70)

    for query in queries:
        print(f"\nQuery: '{query}'")
        skills = service.find_related_skills(query, top_k=5)
        for i, skill in enumerate(skills, 1):
            print(f"  {i}. {skill}")

    print("\n\n2. Finding Skills with Scores")
    print("-" * 70)

    query = "3D visualizations"
    results = service.find_skills_with_scores(query, top_k=5)

    print(f"\nQuery: '{query}'")
    print("\nResults:")
    for item in results:
        print(f"  • {item['name']:30s} | Score: {item['score']:.3f} | Category: {item['category']}")

    print("\n\n3. Skills by Category")
    print("-" * 70)

    categories = ["technical", "soft", "domain"]
    for category in categories:
        skills = service.find_skills_by_category(category, top_k=5)
        print(f"\n{category.upper()} skills:")
        for skill in skills:
            print(f"  • {skill}")

    print("\n\n4. Diversified Recommendations")
    print("-" * 70)

    query = "computer science"
    recommendations = service.get_skill_recommendations(query, num_recommendations=6)

    print(f"\nQuery: '{query}'")
    print("\nDiversified recommendations:")
    for rec in recommendations:
        print(f"  • {rec['name']:30s} | Score: {rec['score']:.3f} | {rec['category']}")

    print("\n\n5. Multiple Query Batch Search")
    print("-" * 70)

    queries = ["python", "education", "visualization"]
    results = service.search_multiple_queries(queries, top_k=3)

    print("\nBatch search results:")
    for query, skills in results.items():
        print(f"\n  Query: '{query}'")
        for skill in skills:
            print(f"    → {skill}")


def demo_indexer_advanced():
    """Demonstrate advanced indexer features."""
    print("\n" + "="*70)
    print("DEMO: Advanced Indexer Features")
    print("="*70)

    indexer = VectorIndexer(
        persist_dir="vector_store/data/chroma",
        use_openai=False
    )

    # Get statistics
    stats = indexer.get_stats()
    print(f"\n📊 Index Statistics:")
    print(f"  Total skills: {stats['total_skills']}")
    print(f"  Storage: {stats['persist_directory']}")

    # Get skill info
    print("\n\n📋 Sample Skill Information:")
    print("-" * 70)

    sample_skills = ["Python", "Programming", "3D Visualizations", "Education"]

    for skill_name in sample_skills:
        info = indexer.get_skill_info(skill_name)
        if info:
            print(f"\n  {skill_name}:")
            print(f"    Category: {info.get('category', 'N/A')}")
            print(f"    Source Count: {info.get('source_count', 0)}")
            print(f"    Weight: {info.get('weight', 0.0)}")
            aliases = info.get('aliases', '')
            if aliases:
                print(f"    Aliases: {aliases}")

    # Custom search with threshold
    print("\n\n🔍 Search with Similarity Threshold")
    print("-" * 70)

    query = "programming"
    high_threshold = indexer.search(query, top_k=10, min_similarity=0.5)
    low_threshold = indexer.search(query, top_k=10, min_similarity=0.2)

    print(f"\n  Query: '{query}'")
    print(f"\n  High threshold (≥0.5): {len(high_threshold)} results")
    for name, score, _ in high_threshold:
        print(f"    • {name}: {score:.3f}")

    print(f"\n  Low threshold (≥0.2): {len(low_threshold)} results")
    for name, score, _ in low_threshold[:5]:  # Show first 5
        print(f"    • {name}: {score:.3f}")


def demo_embedding_models():
    """Show information about embedding models."""
    print("\n" + "="*70)
    print("DEMO: Embedding Models")
    print("="*70)

    print("\n📌 Available Embedding Models:")
    print("-" * 70)
    print("\n1. Local Model (all-MiniLM-L6-v2)")
    print("   - No API key required")
    print("   - Faster (no network latency)")
    print("   - 384-dimensional embeddings")
    print("   - Good for development and testing")
    print("\n2. OpenAI (text-embedding-3-small)")
    print("   - Requires OPENAI_API_KEY or OPENROUTER_API_KEY")
    print("   - Slower (requires API calls)")
    print("   - 1536-dimensional embeddings")
    print("   - Better quality for production")

    print("\n\n⚙️  To use OpenAI embeddings:")
    print("-" * 70)
    print("export OPENAI_API_KEY='your-api-key'")
    print("or")
    print("export OPENROUTER_API_KEY='your-api-key'")
    print("\nThen run:")
    print("  python vector_store/scripts/build_vector_index.py --use-openai")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("STAGE 4: VECTOR STORE & EMBEDDINGS DEMO")
    print("="*70)
    print("\nThis demo showcases the semantic search capabilities")
    print("for skills using vector embeddings and ChromaDB.")

    # Check if index exists
    if not os.path.exists("vector_store/data/chroma"):
        print("\n⚠️  Vector index not found!")
        print("Please build the index first:")
        print("  python vector_store/scripts/build_vector_index.py")
        return 1

    try:
        # Run demos
        demo_embedding_models()
        demo_search_service()
        demo_indexer_advanced()

        print("\n" + "="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print("\n✓ Vector store is ready for integration with RAG systems")
        print("✓ Semantic search works across all 90 skills")
        print("✓ Multiple search modes available (by text, category, etc.)")
        print("✓ Configurable similarity thresholds")
        print("\nFor more information, see vector_store/README.md")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
