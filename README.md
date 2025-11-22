# VR Recommender System

An intelligent VR app recommendation system for CMU Heinz College that combines RAG (Retrieval-Augmented Generation), knowledge graphs, and vector search to provide personalized Meta Quest VR app recommendations based on student learning goals.

## Project Overview

This system was developed in 6 stages to create a comprehensive recommendation pipeline:

1. **Data Collection** - CMU course and VR app data gathering
2. **Skill Extraction** - LLM-based skill and category mapping
3. **Knowledge Graph** - Neo4j graph database for courses, apps, and skills
4. **Vector Store** - ChromaDB semantic search for skill embeddings
5. **RAG Retrieval** - Combined vector search and graph queries
6. **Chatbot Integration** - Flask API with RAG backend

## Features

- **Intelligent Recommendations**: RAG system combining knowledge graph traversal and vector similarity search
- **232 CMU Courses**: Data from 6 departments including SCS, Heinz, Dietrich, CFA, Engineering, and Science
- **77 VR Applications**: Curated Meta Quest apps across education, training, productivity, and fitness
- **90 Skills**: Extracted skills with semantic embeddings for intelligent matching
- **LLM-Powered Understanding**: Query understanding and recommendation reasoning via OpenRouter
- **REST API**: Flask-based API with chatbot interface
- **Session Management**: Chat history tracking and context-aware conversations

## Development Stages

### Stage 1: Data Collection (COMPLETE)
- Built CMU course fetching infrastructure using Firecrawl API
- Implemented VR app data collection with Tavily API
- Created structured JSON outputs for 232 courses and 77 VR apps
- Multi-department support covering 6 CMU colleges
- **Output**: `data_collection/data/courses.json`, `data_collection/data/vr_apps.json`

### Stage 2: Skill Extraction (COMPLETE)
- LLM-based recommendation engine using OpenRouter API (Qwen model)
- Intent-to-category mapping with 17 canonical learning categories
- Skill/interest extraction from user queries
- Flask REST API with `/chat`, `/health`, and root endpoints
- MongoDB analytics pipeline for recommendation tracking
- **Output**: `vr_recommender.py`, `flask_api.py`

### Stage 3: Knowledge Graph (COMPLETE)
- Neo4j graph database with Course, VRApp, and Skill nodes
- TEACHES, DEVELOPS, and RECOMMENDS relationships with weights
- Smart recommendation algorithm based on weighted skill similarity
- Cypher query interface for graph traversal
- **Output**: `knowledge_graph/src/knowledge_graph/` module

### Stage 4: Vector Store (COMPLETE)
- ChromaDB vector store for persistent skill embeddings
- Local embeddings (sentence-transformers) and OpenAI support
- Semantic search with similarity thresholds and category filtering
- Batch search and diversified recommendations
- **Output**: `vector_store/src/vector_store/` module, `vector_store/data/chroma/`

### Stage 5: RAG Retrieval (COMPLETE)
- RAGRetriever combining ChromaDB vector search with Neo4j graph queries
- LLM-based ranking and explanation generation
- Pipeline: Query Understanding -> Vector Search -> Graph Query -> LLM Ranking
- Sub-2-second retrieval latency
- **Output**: `src/rag/` module

### Stage 6: Chatbot Integration (COMPLETE)
- Integrated RAG system with Flask API maintaining backward compatibility
- Chat session management with message history
- Update script for system maintenance
- Production-ready with complete API compatibility
- **Output**: Updated `vr_recommender.py`, `flask_api.py`, `src/chat/`

## Quick Start

### Prerequisites

- Python 3.9+
- Neo4j database
- Required API keys (see Environment Setup)

### One-Command Start

```bash
# Start all services (Neo4j + Flask API)
./start_project.sh

# Or specify a custom port
./start_project.sh 5001

# Force restart all services
./start_project.sh --force
```

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   # Required
   export OPENROUTER_API_KEY="your-openrouter-api-key"

   # Neo4j (required for RAG)
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your-password"

   # Optional
   export PORT=5000
   export OPENROUTER_MODEL="qwen/qwen3-next-80b-a3b-thinking"
   ```

3. **Start Neo4j**:
   ```bash
   # Using Docker
   docker run -p7687:7687 -p7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:latest

   # Or using local installation
   neo4j start
   ```

4. **Build the RAG system** (first time only):
   ```bash
   # Build knowledge graph
   python knowledge_graph/scripts/build_graph.py

   # Build vector index
   python vector_store/scripts/build_vector_index.py
   ```

5. **Start the Flask API**:
   ```bash
   python flask_api.py
   ```

## API Endpoints

### Health Check
```bash
GET /health
```
Response: `{"status": "healthy", "recommender": "ready"}`

### Get Recommendations
```bash
POST /chat
Content-Type: application/json

{"message": "I want to learn machine learning for public policy"}
```

Response includes VR app recommendations with:
- App names and categories
- Likeliness scores (0.0-1.0)
- Matched skills
- LLM-generated reasoning

### Chatbot Interface
```bash
GET /
```
Returns the chatbot HTML interface.

## Usage Examples

### Using the API

```bash
# Get VR app recommendations
curl -X POST http://localhost:5000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "data visualization and analytics"}'

# Check system health
curl http://localhost:5000/health
```

### Using Python

```python
from vr_recommender import HeinzVRLLMRecommender, StudentQuery

# Initialize recommender
recommender = HeinzVRLLMRecommender()

# Create query
query = StudentQuery(
    query="machine learning for public policy",
    interests=["data analysis", "policy"],
    background="MSPPM student"
)

# Get recommendations
result = recommender.generate_recommendation(query)

# Print results
print(result["message"])
for app in result["vr_apps"]:
    print(f"{app['app_name']}: {app['reasoning']}")

# Cleanup
recommender.close()
```

### Using RAG Service Directly

```python
from src.rag.service import RAGService

service = RAGService()
result = service.recommend("Python programming for beginners", top_k=5)

for app in result.apps:
    print(f"{app.name} ({app.category}) - Score: {app.score}")
    print(f"  Skills: {app.matched_skills}")
    print(f"  Why: {app.reasoning}")

service.close()
```

## Architecture

```
User Query (Flask /chat)
    |
    v
Query Understanding (LLM)
    |
    v
Vector Search (ChromaDB)
    |-- Find related skills (top_k=15)
    |-- Return skill list with scores
    |
    v
Neo4j Graph Query
    |-- MATCH (s:Skill)<-[d:DEVELOPS]-(a:VRApp)
    |-- Filter by found skills
    |-- Sum weights per app
    |
    v
LLM Ranking (OpenRouter)
    |-- Generate reasoning
    |-- Re-rank by relevance
    |
    v
JSON Response with Recommendations
```

## VR App Categories

The system includes 77 VR apps across these categories:

- **Education**: InMind, Unimersiv, Mission ISS, VEDAVI VR Human Anatomy
- **Training**: MEL Science VR, Chemistry Lab, 3D Organon VR Anatomy
- **Productivity**: Horizon Workrooms, Spatial, Immersed, Virtual Desktop
- **Data/ML**: Virtualitics VR, DataVR, Neural Explorer VR, Tableau VR
- **Design**: Gravity Sketch, Tilt Brush, ShapesXR
- **Security**: Cyber Range VR, Security Training VR
- **Policy**: PolicyVR, Virtual Town Hall

## System Maintenance

### Update RAG System

```bash
# Full rebuild
python scripts/update_rag.py --source all --rebuild-graph --rebuild-embeddings

# Update only data sources
python scripts/update_rag.py --source courses

# Rebuild only vector index
python scripts/update_rag.py --rebuild-embeddings
```

### Rebuild Knowledge Graph

```bash
# Test connection
python knowledge_graph/scripts/build_graph.py --test

# Build graph
python knowledge_graph/scripts/build_graph.py

# Clear and rebuild
python knowledge_graph/scripts/build_graph.py --clear
```

### Rebuild Vector Index

```bash
# With local embeddings
python vector_store/scripts/build_vector_index.py

# With OpenAI embeddings
python vector_store/scripts/build_vector_index.py --use-openai

# Show statistics
python vector_store/scripts/build_vector_index.py --stats
```

## Project Structure

```
vr-recommender/
├── vr_recommender.py          # Main recommender (RAG-based)
├── flask_api.py               # REST API server
├── start_project.sh           # One-command startup script
├── requirements.txt           # Python dependencies
├── setup.sh                   # MongoDB/Neo4j setup
│
├── src/
│   ├── rag/                   # RAG retrieval system
│   │   ├── models.py          # Data models
│   │   ├── retriever.py       # Vector + graph retrieval
│   │   ├── ranker.py          # LLM ranking
│   │   └── service.py         # Main RAG service
│   └── chat/                  # Chat session management
│       └── session.py
│
├── data_collection/           # Data collection
│   ├── src/data_collection/   # Fetchers for courses/apps
│   └── data/                  # JSON output files
│
├── knowledge_graph/           # Knowledge graph
│   └── src/knowledge_graph/   # Neo4j graph module
│
├── vector_store/              # Vector store
│   ├── src/vector_store/      # ChromaDB module
│   └── data/chroma/           # Persistent embeddings
│
├── scripts/
│   ├── update_rag.py          # RAG system updater
│   └── test_rag.py            # RAG tests
│
└── stage-dev/                 # Development documentation
    └── stage-*-dev-complete.md
```

## Dependencies

Core dependencies (see `requirements.txt` for full list):

- **LLM Integration**: `openai` (for OpenRouter API)
- **Graph Database**: `neo4j`
- **Vector Store**: `chromadb`, `sentence-transformers`
- **Web Framework**: `flask`, `flask-cors`
- **Data Collection**: `firecrawl`, `tavily`
- **Utilities**: `python-dotenv`, `numpy`, `gunicorn`

## Performance

- **Vector Search**: < 50ms per query
- **Neo4j Query**: < 500ms per query
- **Total Retrieval**: < 2 seconds
- **Index Build**: ~15 seconds (local) / ~30 seconds (OpenAI)
- **Database Size**: < 15MB total

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check if Neo4j is running
nc -z localhost 7687 && echo "Neo4j is running" || echo "Neo4j is not running"

# Start Neo4j
neo4j start
```

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Missing Environment Variables
Ensure all required environment variables are set:
```bash
echo $OPENROUTER_API_KEY
echo $NEO4J_URI
echo $NEO4J_USER
echo $NEO4J_PASSWORD
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
