"""
Flask API for OpenRouter LLM-based VR App Recommender (Heinz College)
Returns ONLY VR app recommendations (NO course recommendations)
"""

from flask import Flask, request, jsonify, send_file, make_response, session, redirect, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import sys
import uuid
import time
import functools
import secrets

# Load environment variables
load_dotenv()

# Make local imports work when running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ⬇️ Use the LLM-based recommender
from vr_recommender import HeinzVRLLMRecommender, StudentQuery
from src.logging_service import InteractionLogger
from src.data_manager import JobManager

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
CORS(app, supports_credentials=True)

# --------------------------- Rate Limiter Setup --------------------------- #
# Use Redis if available (env var), otherwise fall back to memory
redis_url = os.getenv("REDIS_URL")
storage_uri = redis_url if redis_url else "memory://"

print("\n" + "=" * 70)
print("INITIALIZING HEINZ RAG VR APP RECOMMENDER")
print(f"Rate Limiter Storage: {storage_uri}")
print("=" * 70)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=storage_uri
)

# Initialize services
recommender = None
interaction_logger = None
data_manager = None

try:
    print("\n🔄 Initializing Services...")
    interaction_logger = InteractionLogger()
    print("✓ Database Logger ready")
    
    data_manager = JobManager()
    print("✓ Data Manager ready")
    
    # Requires Neo4j, ChromaDB, and OPENROUTER_API_KEY
    recommender = HeinzVRLLMRecommender()
    print("✓ RAG VR Recommender ready!")
except Exception as e:
    print(f"❌ Init failed: {e}")
    recommender = None

# --------------------------- Auth Decorator --------------------------- #

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            # If it's an API call, return 401 JSON
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized", "login_required": True}), 401
            # If it's a page load, redirect to login page (or let frontend handle it via 401)
            return send_file("admin_dashboard.html", mimetype="text/html") 
        return f(*args, **kwargs)
    return decorated_function

# --------------------------- Public Endpoints --------------------------- #

@app.route("/", methods=["GET"])
def home():
    """Serve chatbot HTML (if present) or a simple status JSON."""
    print("\n📄 GET / - Serving chatbot")
    try:
        return send_file("vr-chatbot-embed.html", mimetype="text/html")
    except Exception as e:
        return jsonify(
            {
                "status": "running",
                "service": "Heinz LLM VR App Recommender",
                "note": f"HTML not found: {e}",
            }
        )


@app.route("/health", methods=["GET"])
@limiter.exempt
def health():
    """Health check"""
    return jsonify(
        {
            "status": "healthy", 
            "recommender": "ready" if recommender else "unavailable",
            "database": "ready" if interaction_logger else "unavailable",
            "data_manager": "ready" if data_manager else "unavailable"
        }
    )

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute") # Prevent brute force
def login():
    """Admin login endpoint"""
    data = request.get_json(silent=True) or {}
    password = data.get("password")
    
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if not admin_pass:
        return jsonify({"error": "Server misconfigured (ADMIN_PASSWORD missing)"}), 500
        
    if password == admin_pass:
        session['is_admin'] = True
        session.permanent = True
        return jsonify({"success": True, "message": "Logged in"})
    
    return jsonify({"error": "Invalid password"}), 401

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """Admin logout endpoint"""
    session.pop('is_admin', None)
    return jsonify({"success": True})

@app.route("/api/auth/check", methods=["GET"])
def check_auth():
    """Check if current session is admin"""
    return jsonify({"is_admin": session.get('is_admin', False)})


@app.route("/chat", methods=["GET", "POST"])
@limiter.limit("10 per minute") # Protect LLM cost
def chat():
    """Main chat endpoint - returns VR app recommendations"""
    if request.method == "GET":
        return jsonify(
            {
                "hint": 'Use POST with JSON: {"message": "your query"}',
                "example": "curl -X POST http://localhost:5000/chat -H 'Content-Type: application/json' -d '{\"message\": \"machine learning for policy\"}'",
            }
        )

    print("\n" + "=" * 70)
    print("📨 NEW CHAT REQUEST")
    print("=" * 70)
    
    start_time = time.time()

    # 1. Identify User
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
        print(f"👤 New User detected: {user_id}")
    else:
        print(f"👤 Returning User: {user_id}")

    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        
        # Determine session (optional, for now just re-use user_id or generate new per chat load)
        # Simple approach: We consider this a single session unless the frontend sends a session ID.
        session_id = data.get("session_id") or user_id

        print(f"💬 Message: '{message}'")

        if not message:
            return jsonify({"error": "Message required", "type": "error"}), 400

        if not recommender:
            return jsonify(
                {
                    "response": "Recommender unavailable. Please check OPENROUTER_API_KEY configuration.",
                    "type": "error",
                }
            )

        # Parse simple intent
        intent = parse_user_intent(message)
        print(f"🎯 Intent: {intent}")

        response_text = ""
        recommended_apps = []
        
        if intent == "greeting":
            response_text = generate_greeting_response()
        
        elif intent == "help":
            response_text = generate_help_response()

        else:
            # Recommendation path
            print("→ Extracting query data (hints for LLM)…")
            query_data = extract_query_data(message)
            interests = query_data.get("interests", [])
            background = query_data.get("background", "Heinz College student")

            student_query = StudentQuery(query=message, interests=interests, background=background)

            print("\n🔄 Calling recommender.generate_recommendation()…")
            result = recommender.generate_recommendation(student_query)

            recommended_apps = result.get("vr_apps", [])
            print(f"✓ Got {len(recommended_apps)} VR apps")
            
            response_text = format_vr_response(result)

        # Calculate Latency
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # 2. Log Interaction
        if interaction_logger:
            interaction_logger.log_interaction(
                user_id=user_id,
                session_id=session_id,
                query=message,
                response=response_text,
                intent=intent,
                recommended_apps=recommended_apps,
                metadata={"latency_ms": latency_ms, "source": "web_chat"}
            )

        # 3. Send Response (with Cookie)
        print("✅ Sending response\n")
        json_resp = jsonify({"response": response_text, "type": "success", "user_id": user_id})
        resp = make_response(json_resp)
        
        # Set cookie to persist user identity for 30 days
        resp.set_cookie('user_id', user_id, max_age=60*60*24*30, samesite='Lax')
        
        return resp

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"response": f"Error: {str(e)}", "type": "error"}), 500


# --------------------------- Admin API (Protected) --------------------------- #

@app.route("/api/admin/logs", methods=["GET"])
@login_required
def admin_logs():
    """Get paginated interaction logs."""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    user_filter = request.args.get('user_id')
    
    if interaction_logger:
        logs = interaction_logger.get_admin_logs(limit, offset, user_filter)
        return jsonify({"logs": logs, "count": len(logs)})
    return jsonify({"error": "Logger unavailable"}), 503

@app.route("/api/admin/stats", methods=["GET"])
@login_required
def admin_stats():
    """Get system stats."""
    if interaction_logger:
        stats = interaction_logger.get_admin_stats()
        return jsonify(stats)
    return jsonify({"error": "Logger unavailable"}), 503


@app.route("/api/admin/data/status", methods=["GET"])
@login_required
def data_status():
    """Get data file status and current job info."""
    if data_manager:
        return jsonify(data_manager.get_data_stats())
    return jsonify({"error": "Data Manager unavailable"}), 503

@app.route("/api/admin/data/update/courses", methods=["POST"])
@login_required
def update_courses():
    """Trigger course update job."""
    if not data_manager:
        return jsonify({"error": "Data Manager unavailable"}), 503
        
    params = request.get_json(silent=True) or {}
    result = data_manager.start_update_job("courses", params)
    
    if "error" in result:
        return jsonify(result), 409 # Conflict
    return jsonify(result), 202 # Accepted

@app.route("/api/admin/data/update/apps", methods=["POST"])
@login_required
def update_apps():
    """Trigger VR app update job."""
    if not data_manager:
        return jsonify({"error": "Data Manager unavailable"}), 503
        
    params = request.get_json(silent=True) or {}
    result = data_manager.start_update_job("vr_apps", params)
    
    if "error" in result:
        return jsonify(result), 409
    return jsonify(result), 202

@app.route("/api/admin/data/process/skills", methods=["POST"])
@login_required
def process_skills():
    """Trigger skill extraction job."""
    if not data_manager:
        return jsonify({"error": "Data Manager unavailable"}), 503
        
    params = request.get_json(silent=True) or {}
    result = data_manager.start_update_job("skills", params)
    
    if "error" in result:
        return jsonify(result), 409
    return jsonify(result), 202

@app.route("/api/admin/data/process/graph", methods=["POST"])
@login_required
def process_graph():
    """Trigger knowledge graph build job."""
    if not data_manager:
        return jsonify({"error": "Data Manager unavailable"}), 503
        
    params = request.get_json(silent=True) or {}
    result = data_manager.start_update_job("graph", params)
    
    if "error" in result:
        return jsonify(result), 409
    return jsonify(result), 202

# --------------------------- Admin Pages (Protected) --------------------------- #

@app.route("/admin", methods=["GET"])
def admin_dashboard():
    """Serve the Admin Dashboard."""
    print("\n📊 GET /admin - Serving Dashboard")
    # We don't enforce strict login_required here to allow the frontend to load 
    # and show the login modal if needed. 
    # The API calls made by the dashboard will fail if not logged in.
    try:
        return send_file("admin_dashboard.html", mimetype="text/html")
    except Exception as e:
        return jsonify({"error": f"Dashboard not found: {e}"}), 404

@app.route("/admin/data", methods=["GET"])
def admin_data():
    """Serve the Data Management Dashboard."""
    print("\n📊 GET /admin/data - Serving Data Dashboard")
    try:
        return send_file("admin_data.html", mimetype="text/html")
    except Exception as e:
        return jsonify({"error": f"Data Dashboard not found: {e}"}), 404


# --------------------------- Helpers --------------------------- #

def parse_user_intent(message: str) -> str:
    """Determine user intent using word boundary matching"""
    import re
    msg_lower = message.lower()
    
    # Regex for greeting: matches 'hi', 'hello', 'hey' as whole words
    if re.search(r'\b(hello|hi|hey)\b', msg_lower):
        return "greeting"
        
    # Regex for help: matches 'help', 'how to', 'what can'
    if re.search(r'\b(help)\b|how to|what can', msg_lower):
        return "help"
        
    return "recommendation"


def extract_query_data(message: str) -> dict:
    """Extract query data (RAG handles this internally, so simplified)."""
    return {
        "interests": [],
        "background": "CMU Heinz College student"
    }


def generate_greeting_response() -> str:
    return """Hello! I'm your Heinz College VR App Recommender! 🥽

I use an AI model to understand what you're studying and match you with the best VR apps.

Try something like:
• \"I'm learning Python programming\"
• \"Cybersecurity tools\"
• \"Data visualization help\"

What are you working on?"""


def generate_help_response() -> str:
    return """🤖 How I Work:

I use RAG (Retrieval-Augmented Generation) to understand your learning goals. I search a knowledge graph of skills and courses to find the best VR apps for your needs.

**What I Recommend:**
• Meta Quest VR apps for hands-on learning
• Tools matched to your specific interests
• Detailed reasoning for each recommendation

**How to Use:**
Just tell me what you're studying! For example:
• \"machine learning projects\"
• \"policy analysis\"
• \"software engineering\"

Ready to find your perfect VR app?"""


def format_vr_response(result: dict) -> str:
    """Format VR app recommendations for display"""
    vr_apps = result.get("vr_apps", [])
    query = result.get("student_query", "your interests")

    if not vr_apps:
        return (
            f"I couldn't find specific VR apps for '{query}'. "
            f"Try a different phrasing like 'cyber security projects' or 'data analytics tools'."
        )

    # Check if we have mainly bridged results to adjust tone
    has_bridged = any(app.get("retrieval_source") == "semantic_bridge" for app in vr_apps)
    
    response = ""
    if has_bridged and all(app.get("retrieval_source") == "semantic_bridge" for app in vr_apps):
        response = f"I didn't find apps explicitly for **{query}**, but based on related skills, here are some recommendations:\n\n"
    else:
        response = f"Based on your interest in **{query}**, here are VR apps that align with your goals:\n\n"
        
    response += "🥽 **Recommended VR Apps for Meta Quest:**\n\n"

    high_score = [app for app in vr_apps if app["likeliness_score"] >= 0.60] # Lowered slightly
    med_score = [app for app in vr_apps if 0.30 <= app["likeliness_score"] < 0.60]
    
    # Fallback if scores are all low due to bridging penalty
    if not high_score and med_score:
        high_score = med_score
        med_score = []

    if high_score:
        response += "**Top Picks:**\n"
        for app in high_score[:5]:
            match_text = f"{app['likeliness_score']*100:.0f}% match"
            response += f"• **{app['app_name']}** — {app['category']} ({match_text})\n"
            
            # Display Reasoning or Bridge Explanation
            if app.get("retrieval_source") == "semantic_bridge":
                reason = app.get("bridge_explanation", "Related topic")
                response += f"  *↪ {reason}*\n"
            elif app.get("reasoning"):
                 # Optional: Show LLM reasoning if it's not too long
                 pass 
        response += "\n"

    if med_score:
        response += "**Also Consider:**\n"
        for app in med_score[:3]:
            response += f"• {app['app_name']} — {app['category']} ({app['likeliness_score']*100:.0f}% match)\n"
            if app.get("retrieval_source") == "semantic_bridge":
                response += f"  *↪ {app.get('bridge_explanation', 'Related')}\n"
        response += "\n"

    response += "---\n"
    if has_bridged:
        response += "💡 *Some results are inferred based on skill similarity (Semantic Bridge).*\n"
    else:
        response += "💡 *Recommendations are generated by RAG system combining knowledge graph and vector search.*\n"
        
    response += "💬 Want details on any app? Just ask!"

    return response

ALLOWED_HINT_WORDS = {
    # study/learn verbs
    "learn","learning","study","studying","project","projects","practice","practicing","help","tools","apps","app",
    # core topics (broad gate, not exhaustive)
    "cyber","security","cybersecurity","infosec","programming","coding","software","swe","python","java",
    "data","analytics","visualization","viz","tableau","ml","machine","learning","ai","policy","economics",
    "cloud","kubernetes","docker","sql","database","risk","management","leadership","communication"
}

def is_supported_learning_query(message: str) -> bool:
    """Return True only if the message looks like a learning/tool-seeking query."""
    m = message.lower()
    # reject obvious chit-chat or unrelated stuff early
    banned_starts = ("hi", "hello", "hey", "what's up", "how are you", "joke", "weather", "news", "sports")
    if any(m.startswith(x) for x in banned_starts):
        return False
    # must contain at least one allowed hint word
    return any(word in m for word in ALLOWED_HINT_WORDS)

# --------------------------- Run Server --------------------------- #

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    print("\n" + "=" * 70)
    print("HEINZ RAG VR APP RECOMMENDER API")
    print("=" * 70)
    print(f"🚀 Starting on http://localhost:{port}")
    print("\n📍 Endpoints:")
    print(f"   GET  http://localhost:{port}/          → Chatbot")
    print(f"   POST http://localhost:{port}/chat      → Get recommendations")
    print(f"   GET  http://localhost:{port}/health    → Health check")
    print("\n💡 Open: http://localhost:{port}")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=port, debug=True)
