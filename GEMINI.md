# VR Recommender System - Gemini Context

This document provides an overview of the **VR Recommender System** project for Gemini context and navigation.

## 📂 Project Structure

The main project is located in the `vr-recommender/` directory.

- **`vr-recommender/`**: Root of the application.
    - **`flask_api.py`**: Main entry point for the Flask REST API.
    - **`vr_recommender.py`**: Core recommender logic integration.
    - **`start_project.sh`**: One-click startup script (Neo4j + Flask).
    - **`src/`**: Source code for RAG, chat, and core logic.
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

The project includes helper scripts for service management:

- **Start All Services:** `./start_project.sh` (Checks Neo4j, clears ports, starts Flask).
- **Background Start:** `./start_services.sh`
- **Stop All:** `./stop_all.sh`
- **Check Status:** `./status.sh`

### Manual Commands

- **Install Dependencies:** `pip install -r requirements.txt` (Note: Ensure `neo4j`, `chromadb`, `sentence-transformers` are installed if missing from the file).
- **Run API:** `python flask_api.py` (Default port: 5000 or 5001).
- **Build Knowledge Graph:** `python knowledge_graph/scripts/build_graph.py`
- **Build Vector Index:** `python vector_store/scripts/build_vector_index.py`

## 🏗 Architecture

The system uses a **RAG (Retrieval-Augmented Generation)** pipeline:

1.  **Query Understanding**: LLM analyzes user intent.
2.  **Vector Search (ChromaDB)**: Retrieves semantically similar skills/courses.
3.  **Knowledge Graph (Neo4j)**: Traverses relationships (VRApp -> DEVELOPS -> Skill).
4.  **Ranking (LLM)**: Ranks candidates and generates explanations.

## 🛠 Key Tech Stack

-   **Language**: Python 3.9+
-   **Web Framework**: Flask
-   **Database**: Neo4j (Graph), ChromaDB (Vector)
-   **LLM Provider**: OpenRouter (Qwen/OpenAI models)
-   **Data Collection**: Firecrawl, Tavily

## 📝 Development Notes

-   **Environment Variables**: stored in `.env` (requires `OPENROUTER_API_KEY`, `NEO4J_URI`, etc.).
-   **Testing**: Use `pytest` (tests located in `tests/` directories of each module).
-   **Logs**: Check `*.log` files in module directories for debugging.
