# VR Recommender System - Gemini Context

This document provides a comprehensive overview of the **VR Recommender System** project for Gemini context and navigation.

## 📂 Project Structure

The main project is located in the `vr-recommender/` directory.

- **`vr-recommender/`**: Root of the application.
    - **`flask_api.py`**: Main entry point for the Flask REST API.
    - **`vr_recommender.py`**: Core recommender logic integration.
    - **`start_project.sh`**: **primary entry point**. One-click startup script (Neo4j + Flask).
    - **`admin_dashboard.html`**: (Stage 19) System configuration and monitoring dashboard.
    - **`src/`**: Source code.
        - **`rag/`**: Retrieval-Augmented Generation module (Retriever, Ranker, Service).
        - **`chat/`**: Chat session management.
    - **`data_collection/`**: Scripts for scraping CMU courses and VR apps (Stage 1).
        - **`data/`**: JSON data files (`courses.json`, `vr_apps.json`).
    - **`knowledge_graph/`**: Neo4j graph database implementation (Stage 3).
        - **`scripts/build_graph.py`**: Script to build/rebuild the knowledge graph.
    - **`vector_store/`**: ChromaDB vector search implementation (Stage 4).
        - **`data/chroma/`**: Persistent vector embeddings.
        - **`scripts/build_vector_index.py`**: Script to build vector indices.
    - **`scripts/`**: Utility scripts for maintaining the RAG system.

## 🚀 Getting Started

**Working Directory:** Always work from within `vr-recommender/`.

```bash
cd vr-recommender
```

### Startup

The project includes helper scripts for service management. **Always try `start_project.sh` first.**

- **Start All Services:** `./start_project.sh` (Checks Neo4j, clears ports 5000/5001, starts Flask).
- **Background Start:** `./start_services.sh`
- **Stop All:** `./stop_all.sh`
- **Check Status:** `./status.sh`
- **Diagnose Issues:** `./diagnose.sh` (Runs comprehensive system checks).

### Manual Commands

- **Install Dependencies:** `pip install -r requirements.txt`
- **Run API:** `python flask_api.py` (Default port: 5000 or 5001).
- **Build Knowledge Graph:** `python knowledge_graph/scripts/build_graph.py`
- **Build Vector Index:** `python vector_store/scripts/build_vector_index.py`

## 🏗 Architecture

The system uses a **RAG (Retrieval-Augmented Generation)** pipeline:

1.  **Query Understanding**: LLM (Gemini 2.0/Qwen) analyzes user intent.
2.  **Vector Search (ChromaDB)**: Retrieves semantically similar skills/courses using `sentence-transformers`.
3.  **Knowledge Graph (Neo4j)**: Traverses relationships (`VRApp` -> `DEVELOPS` -> `Skill` <- `REQUIRES` <- `Course`).
    - Includes "Semantic Bridge" logic for inferring connections.
4.  **Ranking (LLM)**: Ranks candidates and generates transparent reasoning.

## 🛠 Key Tech Stack

-   **Language**: Python 3.9+
-   **Web Framework**: Flask, Gunicorn
-   **Database**: Neo4j (Graph), ChromaDB (Vector), MongoDB (Logs/Analytics - Optional)
-   **LLM Provider**: OpenRouter (Gemini 2.0 Flash, Qwen) - *Recently switched to Gemini 2.0 for I18n and performance.*
-   **Data Collection**: Firecrawl, Tavily

## 🔄 Recent Changes (Git History)

-   **Stage 19 (Current)**: Implemented `admin_dashboard.html` for system config.
-   **Security & Deploy**: Standardization and security hardening (Stages 15-18).
-   **Internationalization**: Enforced English prompts/reasoning while supporting multi-language inputs.
-   **Scoring**: Improved bridge score scaling (vs capping) for better recommendation confidence.

## 📝 Development Notes

-   **Environment Variables**: `.env` (Requires `OPENROUTER_API_KEY`, `NEO4J_URI`, `NEO4J_AUTH`).
-   **Testing**:
    -   `pytest` in module directories.
    -   `./simple_test.html` or `curl` for API testing.
    -   `./diagnose.sh` for environment/dependency checks.
-   **Logs**: Check `logs/flask_api.log` and `flask_5000.log` (if using start script).

## ⚠️ Common Issues

-   **Neo4j Connection**: Ensure Neo4j is running (`neo4j start`) and credentials in `.env` match.
-   **Port Conflicts**: Use `./start_project.sh` to auto-kill processes on 5000/5001, or use `./check_ports.sh`.