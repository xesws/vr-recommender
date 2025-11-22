#!/usr/bin/env python3
"""Main script to build the knowledge graph"""

import argparse
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from knowledge_graph.src.knowledge_graph.builder import KnowledgeGraphBuilder


def main():
    """Main entry point for knowledge graph building"""
    parser = argparse.ArgumentParser(
        description="Build knowledge graph from courses, VR apps, and skills"
    )
    parser.add_argument(
        "--data-dir",
        default="data_collection/data",
        help="Directory containing JSON data files (default: data_collection/data)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before building"
    )
    parser.add_argument(
        "--min-shared-skills",
        type=int,
        default=1,
        help="Minimum shared skills for recommendations (default: 1)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run connection test without building"
    )

    args = parser.parse_args()

    try:
        builder = KnowledgeGraphBuilder()

        if args.test:
            print("\nRunning connection test...\n")
            success = builder.test_build(args.data_dir)
            return 0 if success else 1

        # Build the knowledge graph
        builder.build(
            data_dir=args.data_dir,
            clear=args.clear,
            min_shared_skills=args.min_shared_skills
        )

        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        print(f"\nMake sure Stage 2 has been run and data files exist in {args.data_dir}/", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ Build failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
