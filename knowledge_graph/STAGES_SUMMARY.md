# VR Recommender System - All Stages Complete

## Project Overview

Successfully implemented a complete 3-stage VR learning app recommendation system for CMU Heinz College. The system extracts skills from course descriptions, builds a Neo4j knowledge graph, and generates intelligent VR app recommendations.

## Stage Summary

### Stage 1: Data Collection ✓
**Status**: Complete

**What it does**:
- Fetches CMU course data from web catalogs
- Scrapes Meta Quest VR app data
- Stores in JSON format

**Output**:
- `stage1/data/courses.json` (14 real courses)
- `stage1/data/vr_apps.json` (77 VR apps)

**Key Files**:
- `stage1/src/data_collection/course_fetcher.py`
- `stage1/src/data_collection/vr_app_fetcher.py`

---

### Stage 2: Skill Extraction ✓
**Status**: Complete

**What it does**:
- Uses LLM (OpenRouter) to extract skills from course/app descriptions
- Normalizes and deduplicates skills
- Creates course-skill and app-skill mappings

**Output**:
- `stage1/data/skills.json` (90 unique skills)
- `stage1/data/course_skills.json` (77 mappings)
- `stage1/data/app_skills.json` (79 mappings)

**Key Features**:
- 100+ skill aliases (ML → Machine Learning)
- Automatic categorization (technical/soft/domain)
- Importance weighting (0.0-1.0)

**Key Files**:
- `stage2/src/skill_extraction/extractor.py`
- `stage2/src/skill_extraction/normalizer.py`
- `stage2/src/skill_extraction/deduplicator.py`
- `stage2/src/skill_extraction/pipeline.py`
- `scripts/extract_skills.py`

**Usage**:
```bash
# Quick test
python scripts/extract_skills.py --top 10

# Full extraction
python scripts/extract_skills.py
```

---

### Stage 3: Knowledge Graph ✓
**Status**: Complete

**What it does**:
- Builds Neo4j graph database
- Connects courses, VR apps, and skills
- Computes course-app recommendations

**Graph Structure**:
- **Nodes**: Course (14), VRApp (77), Skill (90)
- **Relationships**: 
  - TEACHES (Course → Skill): 77
  - DEVELOPS (VRApp → Skill): 79
  - RECOMMENDS (Course ↔ VRApp): Computed

**Key Features**:
- Weighted relationship scoring
- Smart recommendation algorithm
- Comprehensive query interface

**Key Files**:
- `stage3/src/knowledge_graph/connection.py`
- `stage3/src/knowledge_graph/schema.py`
- `stage3/src/knowledge_graph/nodes.py`
- `stage3/src/knowledge_graph/relationships.py`
- `stage3/src/knowledge_graph/builder.py`
- `scripts/build_graph.py`

**Usage**:
```bash
# Test connection
python scripts/build_graph.py --test

# Build graph
python scripts/build_graph.py

# Explore in Neo4j Browser (http://localhost:7474)
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Query                          │
│         "I want to learn programming"                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              Stage 3: Knowledge Graph                │
│              (Neo4j Database)                        │
│                                                       │
│  Query: MATCH (c:Course)-[r:RECOMMENDS]->(a:VRApp)  │
│  WHERE c.title CONTAINS "programming"                │
│  RETURN a.name, r.score                              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              VR App Recommendations                   │
│                                                       │
│  1. InMind (Score: 4.2)                             │
│  2. VR Museum Art (Score: 3.8)                       │
│  3. Neural Explorer (Score: 3.5)                     │
└─────────────────────────────────────────────────────┘
```

## Data Flow

```
Stage 1 (Data Collection)
    ↓
[ courses.json, vr_apps.json ]
    ↓
Stage 2 (Skill Extraction)
    ↓
[ skills.json, course_skills.json, app_skills.json ]
    ↓
Stage 3 (Knowledge Graph)
    ↓
[ Neo4j Database with 3 node types + 3 relationship types ]
    ↓
Stage 4 (Recommendation API) [Future]
    ↓
[ RESTful API for recommendations ]
```

## Technology Stack

- **Data Collection**: Python, BeautifulSoup, Selenium
- **Skill Extraction**: OpenRouter LLM (qwen/qwen3-next-80b-a3b-instruct)
- **Knowledge Graph**: Neo4j 5.x
- **Database**: Neo4j (Graph Database)
- **Language**: Python 3.9+
- **Drivers**: neo4j-python-driver

## Key Statistics

### Data Volume
- Courses: 14 (extracted from 962 catalog entries)
- VR Apps: 77
- Skills: 90 (unique, deduplicated)
- Relationships: 201 total

### Top Skills Extracted
1. Programming (8 mentions)
2. Interactive Learning (8 mentions)
3. 3D Visualizations (8 mentions)
4. Education (8 mentions)
5. Educational Content Development (7 mentions)

### Recommendations Generated
- ~45 course-app pairs identified
- Average 2.3 shared skills per recommendation
- Maximum 5 shared skills

## File Structure

```
vr-recommender/
├── stage1/
│   ├── src/
│   │   └── data_collection/
│   │       ├── course_fetcher.py
│   │       └── vr_app_fetcher.py
│   └── data/
│       ├── courses.json
│       └── vr_apps.json
│
├── stage2/
│   ├── src/
│   │   └── skill_extraction/
│   │       ├── extractor.py
│   │       ├── normalizer.py
│   │       ├── deduplicator.py
│   │       └── pipeline.py
│   ├── README.md
│   └── STAGE2_IMPLEMENTATION.md
│
├── stage3/
│   ├── src/
│   │   └── knowledge_graph/
│   │       ├── connection.py
│   │       ├── schema.py
│   │       ├── nodes.py
│   │       ├── relationships.py
│   │       └── builder.py
│   ├── demo_knowledge_graph.py
│   ├── README.md
│   └── STAGE3_IMPLEMENTATION.md
│
├── scripts/
│   ├── extract_skills.py
│   └── build_graph.py
│
├── src/
│   └── models.py
│
└── tests/
    ├── test_skill_extraction.py
    └── test_knowledge_graph.py
```

## Example Cypher Queries

### 1. Find VR Apps for a Course
```cypher
MATCH (c:Course {course_id: "15-112"})-[r:RECOMMENDS]->(a:VRApp)
RETURN a.name, a.category, r.score, r.shared_skills
ORDER BY r.score DESC
LIMIT 5
```

### 2. Find All Resources for a Skill
```cypher
MATCH (n)-[rel]->(s:Skill {name: "Programming"})
RETURN labels(n)[0] as type,
       COALESCE(n.title, n.name) as name,
       rel.weight as importance
ORDER BY rel.weight DESC
```

### 3. Analyze Skill Categories
```cypher
MATCH (s:Skill)
RETURN s.category, count(s) as count
ORDER BY count DESC
```

### 4. Find Courses and Apps with Similar Skills
```cypher
MATCH (c:Course)-[:TEACHES]->(s:Skill)<-[:DEVELOPS]-(a:VRApp)
WITH c, a, count(s) as shared_skills
WHERE shared_skills >= 3
RETURN c.title, a.name, shared_skills
ORDER BY shared_skills DESC
LIMIT 10
```

## Quick Start Guide

### Prerequisites
```bash
# Install Python dependencies
pip install neo4j openai python-dotenv beautifulsoup4 selenium

# Install Neo4j (via Docker recommended)
docker run -p7687:7687 -p7474:7474 -e NEO4J_AUTH=neo4j/password neo4j
```

### Run Stage 2 (Skill Extraction)
```bash
# Quick test with 10 items
python scripts/extract_skills.py --top 10

# Full extraction
python scripts/extract_skills.py
```

### Run Stage 3 (Knowledge Graph)
```bash
# Test Neo4j connection
python scripts/build_graph.py --test

# Build knowledge graph
python scripts/build_graph.py
```

### Explore in Neo4j Browser
```bash
# Open http://localhost:7474 in browser
# Username: neo4j
# Password: password

# Run queries from the browser interface
```

## Testing

### Run All Tests
```bash
# Stage 2 tests
python tests/test_skill_extraction.py

# Stage 3 tests
python stage3/tests/test_knowledge_graph.py
```

### Demonstration
```bash
# Stage 2 demo
python test_pipeline_quick.py

# Stage 3 demo
python stage3/demo_knowledge_graph.py
```

## Next Steps (Stage 4 - Future)

### Recommendation API
- RESTful endpoints for recommendations
- Real-time query processing
- User preference integration

### Enhanced Features
- User authentication
- Personalized recommendations
- Learning path generation
- Progress tracking
- Analytics dashboard

## Documentation

- **Stage 1**: README in stage1/
- **Stage 2**: README in stage2/, STAGE2_IMPLEMENTATION.md
- **Stage 3**: README in stage3/, STAGE3_IMPLEMENTATION.md
- **Project**: This file, CLAUDE.md

## Support & Resources

- **Neo4j Browser**: http://localhost:7474
- **Neo4j Documentation**: https://neo4j.com/docs/
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/
- **OpenRouter API**: https://openrouter.ai/docs

## Acknowledgments

Built for CMU Heinz College to help students discover VR learning tools that complement their coursework.

## Conclusion

✓ Stage 1: Data Collection - Complete
✓ Stage 2: Skill Extraction - Complete
✓ Stage 3: Knowledge Graph - Complete

**System Status**: Ready for Stage 4 (Recommendation API)
**Overall Progress**: 3/4 stages complete (75%)

The VR recommender system is fully functional through Stage 3, with a knowledge graph ready for intelligent course-app recommendations!
