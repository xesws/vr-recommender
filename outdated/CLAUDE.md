# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Environment Setup

```bash
# Required: Set your OpenRouter API key
export OPENROUTER_API_KEY="your-api-key-here"

# Optional: MongoDB URI (defaults to localhost:27017)
export MONGODB_URI="mongodb://localhost:27017/"

# Optional: Set model name (defaults to qwen/qwen3-next-80b-a3b-thinking)
export OPENROUTER_MODEL="qwen/qwen3-next-80b-a3b-thinking"

# Optional: Set Flask port (defaults to 5000)
export PORT=5000
```

### Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the VR recommender (standalone)
python vr_recommender.py

# Run the Flask API server
python flask_api.py

# Run analytics on MongoDB data
python analytics.py

# Run the demo analytics
python analytics_demo.py

# Setup MongoDB (macOS/Linux)
./setup.sh
```

## Architecture Overview

This is an **LLM-powered VR app recommendation system** for CMU Heinz College that:

1. Takes student learning queries (e.g., "machine learning for public policy")
2. Uses OpenRouter LLM to map queries to canonical categories
3. Returns curated Meta Quest VR apps with likeliness scores
4. Optionally stores all recommendations in MongoDB for analytics

### Core Components

#### 1. **vr_recommender.py** - Main Recommender Engine
- **`HeinzVRLLMRecommender` class**: Core recommendation logic
  - Uses OpenRouter API with `qwen/qwen3-next-80b-a3b-thinking` model (configurable)
  - Maps user queries to 1-3 canonical categories via LLM
  - Falls back to keyword/alias matching if LLM fails
  - Returns 8 VR apps with 0.0-1.0 likeliness scores

- **Category Mapping** (`vr_app_mappings`): 15 categories including:
  - Programming, Data Science, Machine Learning, Data Analytics
  - Public Policy, Economics, Cybersecurity, Risk Management
  - Project Management, Leadership, Communication
  - Design, Finance, Database, Cloud Computing

- **`StudentQuery` dataclass**: Input model with `query`, `interests`, `background`

#### 2. **flask_api.py** - REST API
- Flask web server with CORS enabled
- **`/chat` endpoint**: Main recommendation interface (POST with JSON `{"message": "query"}`)
- **`/health` endpoint**: Health check
- **`/` endpoint**: Serves optional chatbot HTML

- **Query Processing Flow**:
  1. Validates query is learning-focused (rejects chit-chat)
  2. Extracts interests using keyword matching
  3. Calls `HeinzVRLLMRecommender.generate_recommendation()`
  4. Formats response with high/medium score groupings

#### 3. **analytics.py** - MongoDB Analytics
- **`VRRecommendationAnalytics` class**: MongoDB analytics pipeline
  - Connects to `vr_recommendations.recommendations` collection
  - Provides insights: popular apps, categories, interests, query patterns
  - Uses MongoDB aggregation pipelines for efficiency

- **Key Methods**:
  - `get_app_recommendation_counts()`: Most recommended apps
  - `get_category_recommendation_counts()`: Top categories
  - `get_interest_analysis()`: Which interests appear most
  - `get_high_score_apps()`: Apps with ≥80% scores
  - `generate_comprehensive_report()`: Full analytics export

#### 4. **analytics_demo.py** - Demo & Testing
- Demonstrates recommendation generation
- Shows analytics on sample data

### Data Flow

```
User Query (Flask /chat)
    ↓
Extract interests from text
    ↓
HeinzVRLLMRecommender.generate_recommendation()
    ↓
HeinzVRLLMRecommender.recommend_vr_apps()
    ↓
┌─────────────────────────────────────────┐
│ 1. LLM maps query to categories (temp=0)│
│ 2. Fallback: aliases + keywords         │
│ 3. Default to safe categories if none   │
│ 4. Build app scores from categories     │
│ 5. Sort and return top 8 apps          │
└─────────────────────────────────────────┘
    ↓
Format VR response
    ↓
Optional: Store in MongoDB
    ↓
Return JSON to user
```

## Key Configuration

### OpenRouter Model
- Default: `qwen/qwen3-next-80b-a3b-thinking`
- Temperature: 0 (deterministic)
- Max tokens: 64
- Base URL: `https://openrouter.ai/api/v1`

### MongoDB Schema
Each recommendation stored in `vr_recommendations.recommendations`:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "student_query": {
    "query": "machine learning for policy",
    "interests": ["machine learning", "policy"],
    "background": "Heinz College student"
  },
  "recommendations": [
    {
      "app_name": "Neural Explorer VR",
      "likeliness_score": 0.85,
      "category": "Machine Learning",
      "reasoning": "Mapped via LLM intent understanding"
    }
  ],
  "total_apps_recommended": 8,
  "high_score_apps": 3,
  "categories": ["Machine Learning", "Public Policy"]
}
```

## Development Notes

### Adding New Categories
Edit `vr_app_mappings` in `HeinzVRLLMRecommender.__init__()`:
```python
"new_category": {
    "apps": ["App 1", "App 2"],
    "keywords": ["keyword1", "keyword2"]
}
```

### Adding Aliases
Update `_category_aliases()` method in `HeinzVRLLMRecommender`:
```python
return {
    "alias": "canonical_category",
    # ...
}
```

### Error Handling
- **MongoDB failures**: Continue without storage (graceful degradation)
- **OpenAI API errors**: Caught and returned as error responses
- **Empty LLM responses**: Falls back to keyword matching
- **Completely empty**: Uses safe defaults (project_management, communication, programming)

### Testing the API

```bash
# Start Flask API
python flask_api.py &

# Test health check
curl http://localhost:5000/health

# Test recommendation
curl -X POST http://localhost:5001/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "I want to learn machine learning for public policy"}'

# Test another query
curl -X POST http://localhost:5001/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "cybersecurity projects"}'
```

### Dependencies
- `openai==2.0.1`: OpenRouter API client
- `pymongo==4.15.3`: MongoDB driver
- `Flask==3.0.3`: Web framework
- `flask-cors==4.0.1`: CORS support
- `gunicorn==23.0.0`: WSGI server (production)

## Important Files

- `vr_recommender.py`: Core recommendation logic (373 lines)
- `flask_api.py`: REST API endpoints (294 lines)
- `analytics.py`: MongoDB analytics (257 lines)
- `analytics_demo.py`: Demo with sample data
- `setup.sh`: MongoDB installation script
- `example_syllabi.json`: Sample course data (unused in current implementation)

## Project Context

This is a production system for CMU Heinz College students to discover VR learning tools. The system:
- Uses LLM for intelligent intent understanding
- Provides curated, high-quality app recommendations
- Scales via MongoDB for analytics
- Exposes a clean REST API for web/mobile integration
