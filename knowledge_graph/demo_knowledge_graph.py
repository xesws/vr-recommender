#!/usr/bin/env python3
"""
Demonstration of Stage 3 Knowledge Graph Module

This script demonstrates the knowledge graph functionality
without requiring a running Neo4j instance.
"""

import json
import os
from typing import Dict, List


def demo_data_summary():
    """Show summary of input data"""
    print("="*60)
    print("STAGE 3 KNOWLEDGE GRAPH DEMONSTRATION")
    print("="*60)

    # Check data files
    data_dir = "stage1/data"
    files = {
        "courses": f"{data_dir}/courses.json",
        "vr_apps": f"{data_dir}/vr_apps.json",
        "skills": f"{data_dir}/skills.json",
        "course_skills": f"{data_dir}/course_skills.json",
        "app_skills": f"{data_dir}/app_skills.json"
    }

    print("\n📊 Input Data Summary:")
    print("-" * 60)

    for name, path in files.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            print(f"  ✓ {name:20s}: {len(data):4d} records - {path}")
        else:
            print(f"  ✗ {name:20s}: NOT FOUND - {path}")


def demo_knowledge_graph_structure():
    """Demonstrate the knowledge graph structure"""
    print("\n" + "="*60)
    print("KNOWLEDGE GRAPH STRUCTURE")
    print("="*60)

    print("""

    The knowledge graph consists of:

    1. NODES (Entities)
    ┌─────────────┐  ┌──────────┐  ┌─────────┐
    │   Course    │  │  VRApp   │  │  Skill  │
    │             │  │          │  │         │
    │ • course_id │  │ • app_id │  │ • name  │
    │ • title     │  │ • name   │  │ • cat   │
    │ • dept      │  │ • cat    │  │ • count │
    └─────────────┘  └──────────┘  └─────────┘

    2. RELATIONSHIPS (Connections)
    ┌──────────┐              ┌─────────┐              ┌──────────┐
    │  Course  │──TEACHES──→  │  Skill  │←─DEVELOPS──  │  VRApp   │
    │          │  weight      │         │  weight      │          │
    └──────────┘              └─────────┘              └──────────┘
              ╲                                    ╱
               ╲                                  ╱
                ╲                                ╱
                 ↘                              ↙
              ┌──────────────────────────────────┐
              │         RECOMMENDS               │
              │  score, shared_skills, count     │
              └──────────────────────────────────┘

    3. Cypher Query Examples:
    """)

    queries = [
        {
            "title": "Find VR Apps for a Course",
            "query": """
MATCH (c:Course {course_id: "15-112"})-[r:RECOMMENDS]->(a:VRApp)
RETURN a.name, r.score, r.shared_skills
ORDER BY r.score DESC
LIMIT 5
"""
        },
        {
            "title": "Find All Resources for a Skill",
            "query": """
MATCH (n)-[rel]->(s:Skill {name: "Programming"})
RETURN labels(n)[0] as type,
       COALESCE(n.title, n.name) as name,
       rel.weight as importance
ORDER BY rel.weight DESC
"""
        },
        {
            "title": "Analyze Skill Distribution",
            "query": """
MATCH (s:Skill)
RETURN s.category, count(s) as skill_count
ORDER BY skill_count DESC
"""
        }
    ]

    for i, q in enumerate(queries, 1):
        print(f"\n   Example {i}: {q['title']}")
        print("   " + "-" * 56)
        print(q['query'].strip())


def demo_build_process():
    """Demonstrate the build process"""
    print("\n" + "="*60)
    print("BUILD PROCESS")
    print("="*60)

    steps = [
        ("1. Schema Initialization", [
            "Create unique constraints on Course.course_id",
            "Create unique constraints on VRApp.app_id",
            "Create unique constraints on Skill.name",
            "Create indexes on department, category, etc."
        ]),
        ("2. Node Creation", [
            "Load and create Course nodes",
            "Load and create VRApp nodes",
            "Load and create Skill nodes"
        ]),
        ("3. Relationship Creation", [
            "Create TEACHES relationships (Course → Skill)",
            "Create DEVELOPS relationships (VRApp → Skill)",
            "Compute RECOMMENDS relationships (Course ↔ VRApp)"
        ]),
        ("4. Statistics Generation", [
            "Count nodes and relationships",
            "Find top skills by mentions",
            "Analyze course-app connections",
            "Generate recommendation metrics"
        ])
    ]

    for title, items in steps:
        print(f"\n{title}")
        print("  " + "-" * 56)
        for item in items:
            print(f"  • {item}")


def demo_output_statistics():
    """Show sample output statistics"""
    print("\n" + "="*60)
    print("SAMPLE OUTPUT STATISTICS")
    print("="*60)

    stats = """
📊 Nodes:
   Courses: 8
   VR Apps: 10
   Skills: 90
   Total: 108

🔗 Relationships:
   TEACHES: 77
   DEVELOPS: 79
   RECOMMENDS: 45
   Total: 201

💡 Insights:
   Top 5 skills by mentions:
      1. Programming (domain): 8 mentions
      2. Interactive Learning (technical): 8 mentions
      3. 3D Visualizations (technical): 8 mentions
      4. Education (domain): 8 mentions
      5. Educational Content Development (technical): 7 mentions

   Courses teaching most skills:
      1. Fundamentals of Programming and Computer Science: 15 skills
      2. Principles of Imperative Computation: 12 skills
      ...

   VR apps developing most skills:
      1. InMind: 8 skills
      2. VR Museum Art Through Time: 7 skills
      ...

   Total course-app recommendations: 45
   Average shared skills per recommendation: 2.3
   Maximum shared skills: 5
"""

    print(stats)


def demo_usage_examples():
    """Show usage examples"""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)

    examples = [
        {
            "title": "Command Line",
            "commands": [
                "# Test connection only",
                "python scripts/build_graph.py --test",
                "",
                "# Build with defaults",
                "python scripts/build_graph.py",
                "",
                "# Clear and rebuild",
                "python scripts/build_graph.py --clear",
                "",
                "# Custom settings",
                "python scripts/build_graph.py --min-shared-skills 2"
            ]
        },
        {
            "title": "Python API",
            "code": [
                "from stage3.src.knowledge_graph.builder import KnowledgeGraphBuilder",
                "",
                "# Create builder",
                "builder = KnowledgeGraphBuilder()",
                "",
                "# Build graph",
                "builder.build(",
                "    data_dir='stage1/data',",
                "    clear=False,",
                "    min_shared_skills=1",
                ")",
                "",
                "# Run custom query",
                "result = builder.query('''",
                "    MATCH (c:Course)-[r:RECOMMENDS]->(a:VRApp)",
                "    RETURN c.title, a.name, r.score",
                "    ORDER BY r.score DESC",
                "    LIMIT 10",
                "''')"
            ]
        }
    ]

    for example in examples:
        print(f"\n{example['title']}:")
        print("  " + "-" * 56)
        for line in example['commands' if 'commands' in example else 'code']:
            if line.startswith('#'):
                print(f"  {line}")
            else:
                print(f"  {line}")


def main():
    """Run the complete demonstration"""
    demo_data_summary()
    demo_knowledge_graph_structure()
    demo_build_process()
    demo_output_statistics()
    demo_usage_examples()

    print("\n" + "="*60)
    print("TO RUN ACTUAL BUILD:")
    print("="*60)
    print("""
1. Start Neo4j database:
   • Neo4j Desktop: Start a database
   • Docker: docker run -p7687:7687 -e NEO4J_AUTH=neo4j/password neo4j

2. Set environment variables (optional):
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your-password"

3. Build the knowledge graph:
   python scripts/build_graph.py

4. Explore in Neo4j Browser (http://localhost:7474)
""")

    print("="*60)


if __name__ == "__main__":
    main()
