"""
Flask API for OpenRouter LLM-based VR App Recommender (Heinz College)
Returns ONLY VR app recommendations (NO course recommendations)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys

# Make local imports work when running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ⬇️ Use the LLM-based recommender
from vr_recommender import HeinzVRLLMRecommender, StudentQuery

app = Flask(__name__)
CORS(app)

print("\n" + "=" * 70)
print("INITIALIZING HEINZ OPENROUTER VR APP RECOMMENDER")
print("=" * 70)

# Initialize recommender
recommender = None
try:
    print("\n🔄 Initializing OpenRouter LLM-based VR recommender...")
    # Requires OPENROUTER_API_KEY in env
    recommender = HeinzVRLLMRecommender(
        model_name=os.getenv("OPENROUTER_MODEL", "qwen/qwen3-next-80b-a3b-thinking"),
        base_url="https://openrouter.ai/api/v1"
    )
    print("✓ OpenRouter VR Recommender ready!")
except Exception as e:
    print(f"❌ Init failed: {e}")
    recommender = None


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
def health():
    """Health check"""
    return jsonify(
        {"status": "healthy", "recommender": "ready" if recommender else "unavailable"}
    )


@app.route("/chat", methods=["GET", "POST"])
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

    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()

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

        if not is_supported_learning_query(message):
            return jsonify({
                "response": "This assistant only provides VR app recommendations for learning topics (e.g., cybersecurity, data analytics, programming).",
                "type": "error"
            }), 200
        # Parse simple intent for UX niceties
        intent = parse_user_intent(message)
        print(f"🎯 Intent: {intent}")

        if intent == "greeting":
            response = generate_greeting_response()
            return jsonify({"response": response, "type": "success"})

        if intent == "help":
            response = generate_help_response()
            return jsonify({"response": response, "type": "success"})

       

        # Otherwise: recommendation path
        print("→ Extracting query data (hints for LLM)…")
        query_data = extract_query_data(message)
        interests = query_data.get("interests", [])
        background = query_data.get("background", "Heinz College student")

        print(f"   Extracted interests: {interests}")
        print(f"   Background: {background}")

        student_query = StudentQuery(query=message, interests=interests, background=background)

        print("\n🔄 Calling recommender.generate_recommendation()…")
        result = recommender.generate_recommendation(student_query)

        vr_apps = result.get("vr_apps", [])
        print(f"✓ Got {len(vr_apps)} VR apps")
        if vr_apps:
            print("   Top apps:")
            for app in vr_apps[:3]:
                print(f"     • {app['app_name']} ({app['likeliness_score']*100:.0f}%)")
        else:
            print("   ⚠ NO APPS RETURNED!")

        response = format_vr_response(result)
        print("✅ Sending response\n")
        return jsonify({"response": response, "type": "success"})

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"response": f"Error: {str(e)}", "type": "error"}), 500


# --------------------------- Helpers --------------------------- #

def parse_user_intent(message: str) -> str:
    """Determine user intent"""
    msg_lower = message.lower()
    if any(g in msg_lower for g in ["hello", "hi", "hey"]):
        return "greeting"
    if any(h in msg_lower for h in ["help", "how to", "what can"]):
        return "help"
    return "recommendation"


def extract_query_data(message: str) -> dict:
    """Extract light-weight hints to pass to the LLM (optional, improves mapping)"""
    msg_lower = message.lower()
    interest_map = {
        "machine learning": ["machine learning", "ml", "neural network", "ai model"],
        "artificial intelligence": ["artificial intelligence", "ai", "intelligent systems"],
        "data science": ["data science", "data mining", "big data"],
        "data analytics": ["data analytics", "analytics", "business analytics", "analysis"],
        "data visualization": ["data visualization", "visualization", "tableau", "charts", "viz"],
        "programming": ["programming", "coding", "software", "development", "python", "java", "javascript", "swe"],
        "cybersecurity": ["cybersecurity", "cyber security", "information security", "infosec", "security", "hacking"],
        "public policy": ["public policy", "policy analysis", "government"],
        "project management": ["project management", "agile", "scrum"],
        "finance": ["finance", "financial", "fintech", "trading"],
        "statistics": ["statistics", "statistical", "regression"],
        "database": ["database", "sql", "nosql"],
        "cloud computing": ["cloud", "aws", "azure", "gcp", "devops", "kubernetes", "docker"],
    }

    found_interests = []
    for interest, keywords in interest_map.items():
        if any(k in msg_lower for k in keywords):
            found_interests.append(interest)

    if not found_interests:
        found_interests = ["learning"]

    return {"interests": found_interests[:5], "background": "CMU Heinz College student"}


def generate_greeting_response() -> str:
    return """Hello! I'm your Heinz College VR App Recommender! 🥽

I use an AI model to understand what you're studying and match you with the best VR apps.

Try something like:
• "I'm learning Python programming"
• "Cybersecurity tools"
• "Data visualization help"

What are you working on?"""


def generate_help_response() -> str:
    return """🤖 How I Work:

I use an LLM (OpenRouter) to interpret your learning goals and map them to Heinz-style topics, then I recommend VR apps aligned to those topics.

**What I Recommend:**
• Meta Quest VR apps for hands-on learning
• Tools that match what Heinz students study
• Brief reasons for why each app fits

**How to Use:**
Just tell me what you're studying! For example:
• "machine learning projects"
• "policy analysis"
• "software engineering"

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

    response = f"Based on your interest in **{query}**, here are VR apps that align with your goals:\n\n"
    response += "🥽 **Recommended VR Apps for Meta Quest:**\n\n"

    high_score = [app for app in vr_apps if app["likeliness_score"] >= 0.67]
    med_score = [app for app in vr_apps if 0.33 <= app["likeliness_score"] < 0.67]

    if high_score:
        response += "**Highly Recommended:**\n"
        for app in high_score[:5]:
            response += f"• **{app['app_name']}** — {app['category']} ({app['likeliness_score']*100:.0f}% match)\n"
        response += "\n"

    if med_score:
        response += "**Also Consider:**\n"
        for app in med_score[:3]:
            response += f"• {app['app_name']} — {app['category']} ({app['likeliness_score']*100:.0f}% match)\n"
        response += "\n"

    response += "---\n"
    response += "💡 *Recommendations are generated by an LLM that understands Heinz learning topics.*\n"
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
    print("HEINZ OPENROUTER VR APP RECOMMENDER API")
    print("=" * 70)
    print(f"🚀 Starting on http://localhost:{port}")
    print("\n📍 Endpoints:")
    print(f"   GET  http://localhost:{port}/          → Chatbot")
    print(f"   POST http://localhost:{port}/chat      → Get recommendations")
    print(f"   GET  http://localhost:{port}/health    → Health check")
    print("\n💡 Open: http://localhost:{port}")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=port, debug=True)
