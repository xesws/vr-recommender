# VR Recommender System

An intelligent VR app recommendation system for CMU Heinz College that combines RAG (Retrieval-Augmented Generation), knowledge graphs, and vector search to provide personalized Meta Quest VR app recommendations based on student learning goals.

## 🚀 Quick Start (Recommended)

The project includes a robust all-in-one startup script that handles everything:

```bash
# Start all services (Neo4j + MongoDB + Flask API)
./start_project.sh
```

**What this script does:**
1.  **Checks Environment**: Ensures Python dependencies are installed.
2.  **Starts Databases**: Checks for and starts Neo4j and MongoDB services.
3.  **Cleans Ports**: Automatically frees up ports 5000/5001 if they are in use.
4.  **Launches App**: Starts the Flask API server.
5.  **Shows Logs**: Streams the application logs to your terminal.

### Other Startup Options

*   **Background Mode**: Run `./start_project.sh --background` to start services silently and detach.
*   **Force Restart**: Run `./start_project.sh --force` (or `./restart.sh`) to stop all running instances and restart fresh.
*   **Status Check**: Run `./status.sh` to view the health of all services.
*   **Stop**: Run `./stop_all.sh` to cleanly shut down all services.

### Access Points

*   **Chatbot Interface**: http://localhost:5000/
*   **API Health Check**: http://localhost:5000/health
*   **Neo4j Browser**: http://localhost:7474
*   **Admin Dashboard**: http://localhost:5000/admin (Login required)

## 🏗 Architecture

The system uses a **RAG (Retrieval-Augmented Generation)** pipeline:

1.  **Query Understanding**: LLM (Gemini 2.0) analyzes user intent.
2.  **Vector Search (ChromaDB)**: Retrieves semantically similar skills/courses.
3.  **Knowledge Graph (Neo4j)**: Traverses relationships (`VRApp` -> `DEVELOPS` -> `Skill`).
    *   *New*: Includes "Semantic Bridge" logic to connect unrelated terms.
4.  **Ranking (LLM)**: Ranks candidates and generates transparent reasoning.

## 🛠 Key Tech Stack

-   **Language**: Python 3.9+
-   **Web Framework**: Flask, Gunicorn
-   **Databases**: Neo4j (Graph), ChromaDB (Vector), MongoDB (Data/Logs)
-   **LLM Provider**: OpenRouter (Gemini 2.0 Flash)
-   **Data Collection**: Firecrawl, Tavily

## 📂 Project Structure

```
vr-recommender/
├── flask_api.py               # REST API server
├── vr_recommender.py          # Core RAG logic
├── start_project.sh           # Main entry point
├── requirements.txt           # Python dependencies
├── src/
│   ├── rag/                   # RAG System (Retriever, Ranker)
│   ├── chat/                  # Chat Session Management
│   ├── knowledge_graph/       # Neo4j Graph Builder
│   ├── vector_store/          # ChromaDB Vector Search
│   └── db/                    # MongoDB Repositories
├── data_collection/           # Data Scraping Scripts
└── scripts/                   # Maintenance Utilities
```

## 📝 Development Notes

-   **Environment Variables**: Stored in `.env` (Requires `OPENROUTER_API_KEY`, `NEO4J_URI`, etc.).
-   **Updating Data**: Use the Admin Dashboard (`/admin/data`) to trigger scrapers or rebuild graphs.
-   **Testing**: Run `pytest` or use the `./diagnose.sh` script for system checks.

## License

MIT License - see LICENSE file for details.