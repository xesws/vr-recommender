#!/usr/bin/env python3
"""
Main script for building the skill vector index.

This script:
1. Loads skills from JSON
2. Generates embeddings using specified model
3. Stores in ChromaDB
4. Provides test search functionality
"""

import argparse
import sys
import os

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from vector_store.src.vector_store.indexer import VectorIndexer


def main():
    """Main entry point for building vector index."""
    parser = argparse.ArgumentParser(
        description="Build skill vector index using embeddings"
    )
    parser.add_argument(
        "--skills",
        default="data_collection/data/skills.json",
        help="Path to skills.json file (default: data_collection/data/skills.json)"
    )
    parser.add_argument(
        "--persist-dir",
        default="vector_store/data/chroma",
        help="Directory for ChromaDB persistence (default: vector_store/data/chroma)"
    )
    parser.add_argument(
        "--use-openai",
        action="store_true",
        help="Use OpenAI embeddings instead of local model"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=None,
        help="Specific model name to use"
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear existing index before building"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Test search query after building (e.g., 'machine learning')"
    )
    parser.add_argument(
        "--test-queries",
        nargs="+",
        help="Multiple test queries (space separated)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show index statistics"
    )

    args = parser.parse_args()

    try:
        # Initialize indexer
        indexer = VectorIndexer(
            use_openai=args.use_openai,
            persist_dir=args.persist_dir,
            model_name=args.model_name
        )

        # Build index
        clear_existing = not args.no_clear
        indexer.build_index(args.skills, clear_existing=clear_existing)

        # Show statistics
        if args.stats:
            stats = indexer.get_stats()
            print(f"\nIndex Statistics:")
            print(f"  Total skills: {stats['total_skills']}")
            print(f"  Directory: {stats['persist_directory']}")

        # Run test queries
        test_queries = args.test_queries or ([args.test] if args.test else [])

        if test_queries:
            print(f"\n{'='*60}")
            print(f"TESTING SEARCH")
            print(f"{'='*60}\n")

            for query in test_queries:
                print(f"\nQuery: '{query}'")
                print("-" * 60)
                results = indexer.search(query, top_k=5, min_similarity=0.0)
                for i, (name, score, meta) in enumerate(results, 1):
                    category = meta.get("category", "unknown")
                    print(f"  {i}. {name} (score: {score:.3f}, category: {category})")

        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        print(f"\nMake sure Stage 2 has been run and {args.skills} exists", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Build failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
