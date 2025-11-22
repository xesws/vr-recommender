# Stage 3: Knowledge Graph Construction

## Overview

Stage 3 builds a comprehensive Neo4j knowledge graph connecting courses, VR applications, and skills. This creates a navigable graph database where relationships between educational resources can be explored and recommendations can be computed based on shared skills.

## Purpose

The knowledge graph serves as the bridge between:
- **Courses** (offered at CMU)
- **VR Applications** (learning tools)
- **Skills** (extracted from both courses and apps)

By modeling these as a graph with weighted relationships, we can:
- Find VR apps that complement specific courses
- Discover courses and apps that develop similar skills
- Generate personalized learning path recommendations
- Analyze skill distribution across the curriculum

## Architecture

### Components

1. **Neo4jConnection** (`stage3/src/knowledge_graph/connection.py`)
   - Manages database connection
   - Handles query execution
   - Connection lifecycle management

2. **KnowledgeGraphSchema** (`stage3/src/knowledge_graph/schema.py`)
   - Creates unique constraints for data integrity
   - Creates indexes for query performance
   - Schema validation and cleanup

3. **NodeCreator** (`stage3/src/knowledge_graph/nodes.py`)
   - Creates Course nodes from courses.json
   - Creates VRApp nodes from vr_apps.json
   - Creates Skill nodes from skills.json

4. **RelationshipCreator** (`stage3/src/knowledge_graph/relationships.py`)
   - Creates TEACHES relationships (Course → Skill)
   - Creates DEVELOPS relationships (VRApp → Skill)
   - Computes RECOMMENDS relationships (Course → VRApp)

5. **KnowledgeGraphBuilder** (`stage3/src/knowledge_graph/builder.py`)
   - Orchestrates the complete build process
   - Generates statistics and insights
   - Provides testing and query interfaces

### Data Flow

```
Input JSON Files
    ↓
Neo4j Database
    ├─→ Course Nodes
    ├─→ VRApp Nodes
    ├─→ Skill Nodes
    ↓
Relationships
    ├─→ Course -[TEACHES]-> Skill
    ├─→ VRApp -[DEVELOPS]-> Skill
    └─→ Course -[RECOMMENDS]-> VRApp
    ↓
Queryable Graph for Recommendations
```

## Installation & Setup

### Prerequisites

1. **Neo4j Database** (v4.4 or later)
   - Install from: https://neo4j.com/download/
   - Start Neo4j Desktop or Neo4j Server
   - Default port: 7687

2. **Python Dependencies**
   ```bash
   pip install neo4j python-dotenv
   ```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Neo4j connection settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

Or set environment variables:

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"
```

### Directory Structure

```
stage3/
├── src/
│   └── knowledge_graph/
│       ├── __init__.py
│       ├── connection.py      # Neo4j connection
│       ├── schema.py          # Constraints & indexes
│       ├── nodes.py           # Node creation
│       ├── relationships.py   # Relationship creation
│       └── builder.py         # Main pipeline
├── scripts/
│   └── build_graph.py         # CLI interface
├── tests/
│   └── test_knowledge_graph.py # Unit tests
└── README.md                  # This file
```

## Usage

### Command Line Interface

#### Test Connection (No Build)
```bash
python scripts/build_graph.py --test
```

#### Build Knowledge Graph
```bash
# Build with default settings
python scripts/build_graph.py

# Clear existing data before building
python scripts/build_graph.py --clear

# Build with custom data directory
python scripts/build_graph.py --data-dir /path/to/data

# Build with minimum shared skills filter
python scripts/build_graph.py --min-shared-skills 2
```

#### Combined Options
```bash
# Clear, rebuild with custom settings
python scripts/build_graph.py --clear --data-dir stage1/data --min-shared-skills 1
```

### Python API

```python
from stage3.src.knowledge_graph.builder import KnowledgeGraphBuilder

# Create builder
builder = KnowledgeGraphBuilder()

# Run complete build
builder.build(
    data_dir="stage1/data",
    clear=False,
    min_shared_skills=1
)

# Run connection test only
builder.test_build("stage1/data")

# Execute custom queries
result = builder.query("""
    MATCH (c:Course)-[r:RECOMMENDS]->(a:VRApp)
    RETURN c.title, a.name, r.score
    ORDER BY r.score DESC
    LIMIT 10
""")
```

### Expected Output

When building completes successfully, you'll see:

```
============================================================
KNOWLEDGE GRAPH STATISTICS
============================================================

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
      ...

   Courses teaching most skills:
      1. Fundamentals of Programming and Computer Science: 15 skills
      ...

   VR apps developing most skills:
      1. InMind: 8 skills
      ...

   Total course-app recommendations: 45
   Average shared skills per recommendation: 2.3
   Maximum shared skills: 5
```

## Output Files

The build process populates the Neo4j database (not files). To query the graph:

### Example Cypher Queries

#### Find VR Apps Recommended for a Course

```cypher
MATCH (c:Course {course_id: "15-112"})-[r:RECOMMENDS]->(a:VRApp)
RETURN a.name, a.category, r.score, r.shared_skills
ORDER BY r.score DESC
LIMIT 5
```

#### Find All Resources for a Skill

```cypher
MATCH (n)-[rel]->(s:Skill {name: "Programming"})
RETURN labels(n)[0] as type,
       COALESCE(n.title, n.name) as name,
       rel.weight as importance
ORDER BY rel.weight DESC
```

#### Find Courses and Apps with Similar Skills

```cypher
MATCH (c:Course)-[:TEACHES]->(s:Skill)<-[:DEVELOPS]-(a:VRApp)
WITH c, a, collect(s.name) as shared_skills, count(s) as skill_count
WHERE skill_count >= 3
RETURN c.title, a.name, skill_count, shared_skills
ORDER BY skill_count DESC
LIMIT 10
```

#### Analyze Skill Categories

```cypher
MATCH (s:Skill)
RETURN s.category, count(s) as skill_count, avg(s.source_count) as avg_mentions
ORDER BY skill_count DESC
```

#### Find Highly Connected Skills

```cypher
MATCH (s:Skill)
OPTIONAL MATCH (c:Course)-[tc:TEACHES]->(s)
OPTIONAL MATCH (a:VRApp)-[ad:DEVELOPS]->(s)
WITH s, count(DISTINCT c) as course_count, count(DISTINCT a) as app_count
RETURN s.name, s.category, course_count, app_count, course_count + app_count as total_connections
ORDER BY total_connections DESC
LIMIT 10
```

## Data Models

### Nodes

#### Course
```cypher
(c:Course {
  course_id: "15-112",
  title: "Fundamentals of Programming and Computer Science",
  department: "School of Computer Science",
  description: "A technical introduction to the fundamentals...",
  units: 12
})
```

#### VRApp
```cypher
(a:VRApp {
  app_id: "InMind",
  name: "InMind",
  category: "Education",
  description: "VR game to improve mental health...",
  rating: 4.3,
  price: "Free",
  features: ["Mental Health", "VR", "Education"]
})
```

#### Skill
```cypher
(s:Skill {
  name: "Programming",
  category: "domain",
  aliases: ["Coding", "Software Development"],
  source_count: 8,
  weight: 0.9
})
```

### Relationships

#### TEACHES
```cypher
(c:Course)-[r:TEACHES {
  weight: 0.9,
  created_at: 1234567890
}]->(s:Skill)
```
Indicates the importance of a skill in a course (0.0-1.0)

#### DEVELOPS
```cypher
(a:VRApp)-[r:DEVELOPS {
  weight: 0.8,
  created_at: 1234567890
}]->(s:Skill)
```
Indicates how well an app develops a skill (0.0-1.0)

#### RECOMMENDS
```cypher
(c:Course)-[r:RECOMMENDS {
  score: 4.2,
  shared_skills: ["Programming", "Problem Solving"],
  skill_count: 2,
  created_at: 1234567890
}]->(a:VRApp)
```
Computed relationship based on shared skills and weights

## Features

### 1. Schema Enforcement
- Unique constraints ensure no duplicate nodes
- Indexes optimize query performance
- Automatic schema validation

### 2. Relationship Computation
- Weighted relationships based on skill importance
- Automatic RECOMMENDS calculation using similarity
- Configurable minimum shared skills threshold

### 3. Comprehensive Statistics
- Node and relationship counts
- Top skills by mentions
- Courses/apps with most connections
- Recommendation analysis

### 4. Graph Analytics
- Skill category distribution
- Network connectivity analysis
- Recommendation scoring

## Acceptance Criteria

- [x] Neo4j database contains all Course, VRApp, Skill nodes
- [x] TEACHES relationships connect Course and Skill nodes
- [x] DEVELOPS relationships connect VRApp and Skill nodes
- [x] RECOMMENDS relationships connect Course and VRApp nodes
- [x] Example Cypher queries return expected results
- [x] Graph can be visualized in Neo4j Browser

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest stage3/tests/test_knowledge_graph.py -v

# Or run directly
python stage3/tests/test_knowledge_graph.py
```

### Run Connection Test

```bash
# Test Neo4j connection and data availability
python scripts/build_graph.py --test
```

### Sample Test Results

```
🧪 TEST BUILD
============================================================
✓ All required data files present
✓ Neo4j connection successful
✓ Connection test successful

✓ All tests passed
```

## Troubleshooting

### Connection Issues

**Problem**: `Failed to connect to Neo4j`
```bash
# Check Neo4j is running
neo4j status

# Start Neo4j
neo4j start

# Or using Docker
docker run \
  -p7687:7687 \
  -p7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**Problem**: Authentication failed
```bash
# Verify credentials in .env file
cat .env

# Reset Neo4j password (if needed)
neo4j-admin set-initial-password your-new-password
```

### Data Issues

**Problem**: `FileNotFoundError: courses.json not found`
```bash
# Run Stage 2 first
python scripts/extract_skills.py --top 10

# Verify files exist
ls -la stage1/data/
```

**Problem**: Constraint violations
```bash
# Clear database and rebuild
python scripts/build_graph.py --clear
```

### Query Performance

**Problem**: Slow queries
```bash
# Check if indexes exist
CALL db.indexes()

# Rebuild indexes
CREATE INDEX skill_name IF NOT EXISTS FOR (s:Skill) ON (s.name);
```

## Neo4j Browser

Visualize the graph in Neo4j Browser (http://localhost:7474):

```cypher
// View entire graph
MATCH (n) RETURN n LIMIT 100

// View specific course and recommendations
MATCH path = (c:Course {course_id: "15-112"})-[*1..2]-(n)
RETURN path LIMIT 50
```

## Future Enhancements

1. **Skill Hierarchy**
   - Parent-child skill relationships
   - Skill prerequisite modeling
   - Skill difficulty levels

2. **Temporal Data**
   - Course offering history
   - App version tracking
   - Skill evolution over time

3. **Recommendation Refinement**
   - User preference weighting
   - Collaborative filtering
   - Multi-objective optimization

4. **Graph Algorithms**
   - PageRank for skill importance
   - Community detection for skill clusters
   - Shortest paths for learning progressions

5. **Export Capabilities**
   - GraphML export
   - CSV exports for analysis
   - Visualization generation

## Performance Notes

### Building Process
- **Small dataset** (10 courses, 10 apps, 90 skills): ~1 minute
- **Full dataset** (~14 courses, 77 apps, 200+ skills): ~2-3 minutes

### Query Performance
- Simple queries: <10ms
- Complex traversals: <100ms
- Aggregations: <500ms

### Database Size
- Small graph: ~1MB
- Full graph: ~5-10MB

## Dependencies

```txt
neo4j>=5.0.0
python-dotenv>=0.19.0
```

## References

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Tutorial](https://neo4j.com/developer/python/)
