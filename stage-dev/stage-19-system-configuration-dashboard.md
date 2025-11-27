# Stage 19: System Configuration Dashboard

## 🎯 Objective
Create a new **Configuration Dashboard** (`admin_config.html`) within the Admin interface. This module will allow administrators to dynamically configure system parameters and API keys without needing to modify `.env` files or restart the Docker containers.

## 📋 Requirements
- **New UI Page**: A dedicated "Settings" or "Configuration" page in the Admin dashboard.
- **Manageable Configurations**:
  - **LLM Provider**: OpenRouter API Key, Model Selection (e.g., `google/gemini-2.0-flash-001`, `qwen/qwen-2.5-72b`).
  - **Data Collection**: Firecrawl API Key, Tavily API Key.
  - **Database Settings**: MongoDB Connection URI (View/Update), Neo4j URI.
- **Security**: 
  - API Keys must be masked (e.g., `sk-****`) when displayed.
  - Only authenticated Admins can view or edit.
- **Dynamic Runtime**: Updating a key should immediately affect the running service (hot-reload) without requiring a container restart.

## 🛠 Implementation Plan

### 1. Database Layer (MongoDB)
- **New Collection**: `system_config`
- **Schema Design**: Key-Value pair structure or a singleton document for global settings.
  ```json
  {
    "_id": "global_settings",
    "llm_provider": "openrouter",
    "openrouter_api_key": "sk-...",
    "openrouter_model": "google/gemini-2.0-flash-001",
    "firecrawl_api_key": "fc-...",
    "tavily_api_key": "tv-..."
  }
  ```
- **Repository**: Create `src/db/repositories/config_repo.py`.
  - Methods: `get_config()`, `update_config(key, value)`, `update_bulk(dict)`.

### 2. Backend Logic (`src/config_manager.py`)
- Create a `ConfigManager` class that acts as the "Source of Truth".
- **Priority Logic**: 
  1. Check Database (`system_config` collection).
  2. Fallback to Environment Variables (`os.getenv`).
- **Integration points**:
  - Update `vr_recommender.py` to fetch the API Key/Model from `ConfigManager` instead of `os.getenv`.
  - Update `src/data_manager.py` to fetch Firecrawl/Tavily keys from `ConfigManager`.

### 3. API Endpoints (`flask_api.py`)
- `GET /api/admin/config`: 
  - Returns current configuration.
  - **Crucial**: Mask sensitive keys (return `******` instead of the actual key).
- `POST /api/admin/config`: 
  - Accepts JSON payload to update settings.
  - Validation: Check if keys look valid (basic regex or length check).
  - Trigger a "Hot Reload" of the `recommender` instance if LLM settings change.
- `POST /api/admin/config/test`: 
  - Optional endpoint to verify if a key works (e.g., make a dummy call to OpenRouter).

### 4. Frontend Implementation (`admin_config.html`)
- **Layout**: Clone `admin_dashboard.html` sidebar/header structure.
- **Sections**:
  - **🤖 AI Model Settings**: Dropdown for Model ID, Input for API Key.
  - **🕷️ Data Scrapers**: Inputs for Firecrawl & Tavily.
  - **💾 Database Connections**: Inputs for Mongo/Neo4j (with "Restart Required" warnings if changed).
- **Interactions**:
  - "Save Changes" button (AJAX POST).
  - "Test Connection" buttons (optional).
  - Toast notifications for success/error.

### 5. Verification Steps
1. **UI Check**: Verify the new page loads and looks consistent with the dark mode theme.
2. **Persistence**: Change the Model ID in the UI, restart the Flask app (or container), and ensure the new setting persists (via MongoDB).
3. **Runtime Effect**: Change the API Key to an invalid one, try a chat, verify it fails. Change it back, verify it works.
