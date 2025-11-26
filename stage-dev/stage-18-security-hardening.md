# Stage 18: Security Hardening and Monitoring

## Overview

Secure the VR Recommender application for production deployment with admin authentication, secrets management, rate limiting, and monitoring.

**Status**: Planned
**Priority**: High
**Estimated Duration**: 1 week
**Dependencies**: Stage 16 (MongoDB), Stage 17 (Docker deployment)

---

## Security Issues to Address

| Issue | Current State | Risk Level |
|-------|--------------|------------|
| Admin Dashboard | No authentication | Critical |
| API Keys | Hardcoded in .env | High |
| Rate Limiting | None | High |
| CORS | Wide open (`CORS(app)`) | Medium |
| Audit Logging | None | Medium |
| Input Validation | Basic | Medium |

---

## 1. Admin Authentication

### Implementation: Flask-Login with bcrypt

#### New File: `src/auth.py`

```python
"""
Admin authentication module for VR Recommender.
Single-admin implementation using Flask-Login and bcrypt.
"""

import os
import bcrypt
from functools import wraps
from flask import session, request, redirect, url_for, jsonify, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import timedelta

login_manager = LoginManager()

class AdminUser(UserMixin):
    """Single admin user model."""

    def __init__(self, username: str):
        self.id = username
        self.username = username

    @staticmethod
    def verify_password(password: str) -> bool:
        """Verify password against stored hash."""
        stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
        if not stored_hash:
            return False
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                stored_hash.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def get_admin():
        """Return the admin user."""
        username = os.getenv("ADMIN_USERNAME", "admin")
        return AdminUser(username)


@login_manager.user_loader
def load_user(user_id: str):
    """Load user for Flask-Login."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    if user_id == admin_username:
        return AdminUser(admin_username)
    return None


def admin_required(f):
    """
    Decorator to require admin authentication for routes.
    Returns 401 for API requests, redirects for page requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def init_auth(app):
    """Initialize authentication for Flask app."""
    # Session configuration
    app.config['SECRET_KEY'] = os.getenv(
        'FLASK_SECRET_KEY',
        os.urandom(32).hex()
    )
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

    login_manager.init_app(app)
    login_manager.login_view = 'admin_login'
    login_manager.login_message = 'Please log in to access the admin panel.'
```

#### New File: `templates/admin_login.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - VR Recommender</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            max-width: 400px;
            width: 100%;
            margin: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            border-radius: 12px;
            overflow: hidden;
        }
        .card-header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            padding: 30px;
        }
        .card-header h4 {
            margin: 0;
            font-weight: 600;
        }
        .card-body {
            padding: 30px;
        }
        .form-control:focus {
            border-color: #2a5298;
            box-shadow: 0 0 0 0.2rem rgba(42, 82, 152, 0.25);
        }
        .btn-primary {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            border: none;
            padding: 12px;
            font-weight: 600;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        }
    </style>
</head>
<body>
    <div class="login-card card">
        <div class="card-header text-white text-center">
            <h4><i class="bi bi-shield-lock me-2"></i>Heinz VR Admin</h4>
            <small class="text-light opacity-75">VR Recommender System</small>
        </div>
        <div class="card-body">
            {% if error %}
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            {% endif %}

            <form method="POST" action="{{ url_for('admin_login') }}">
                <div class="mb-3">
                    <label class="form-label">
                        <i class="bi bi-person me-1"></i>Username
                    </label>
                    <input type="text" name="username" class="form-control"
                           placeholder="Enter username" required autofocus>
                </div>
                <div class="mb-4">
                    <label class="form-label">
                        <i class="bi bi-key me-1"></i>Password
                    </label>
                    <input type="password" name="password" class="form-control"
                           placeholder="Enter password" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">
                    <i class="bi bi-box-arrow-in-right me-2"></i>Login
                </button>
            </form>
        </div>
        <div class="card-footer text-center text-muted py-3">
            <small>CMU Heinz College VR Learning Initiative</small>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

#### Modify `flask_api.py`

Add authentication to admin routes:

```python
# Add imports at top of flask_api.py
from flask_login import login_user, logout_user, current_user
from src.auth import init_auth, admin_required, AdminUser

# After app = Flask(__name__)
init_auth(app)

# Add login/logout routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        expected_username = os.getenv("ADMIN_USERNAME", "admin")

        if username == expected_username and AdminUser.verify_password(password):
            user = AdminUser(username)
            login_user(user, remember=True)

            # Log successful login
            from src.audit_logger import log_admin_action
            log_admin_action("login", {"ip": request.remote_addr})

            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))

        # Log failed attempt
        from src.audit_logger import log_security_event
        log_security_event("login_failed", "medium", {
            "username": username,
            "ip": request.remote_addr
        })
        error = "Invalid username or password"

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
@admin_required
def admin_logout():
    """Admin logout."""
    from src.audit_logger import log_admin_action
    log_admin_action("logout", {"ip": request.remote_addr})

    logout_user()
    return redirect(url_for('admin_login'))


# Protect existing admin routes with @admin_required decorator
@app.route("/admin", methods=["GET"])
@admin_required  # ADD THIS
def admin_dashboard():
    # ... existing code ...

@app.route("/admin/data", methods=["GET"])
@admin_required  # ADD THIS
def admin_data():
    # ... existing code ...

@app.route("/api/admin/logs", methods=["GET"])
@admin_required  # ADD THIS
def admin_logs():
    # ... existing code ...

@app.route("/api/admin/stats", methods=["GET"])
@admin_required  # ADD THIS
def admin_stats():
    # ... existing code ...

# ... protect all /api/admin/* routes ...
```

#### Password Hash Generation Script

**New File**: `scripts/generate_admin_password.py`

```python
#!/usr/bin/env python3
"""
Generate bcrypt hash for admin password.
Usage: python scripts/generate_admin_password.py <password>
"""

import bcrypt
import sys
import getpass

def generate_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Enter admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match")
            sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    hash_value = generate_hash(password)

    print("\n" + "=" * 50)
    print("Add the following to your .env file:")
    print("=" * 50)
    print(f"ADMIN_PASSWORD_HASH={hash_value}")
    print("=" * 50)
```

---

## 2. Rate Limiting

### Implementation: Flask-Limiter

#### New File: `src/rate_limiter.py`

```python
"""
Rate limiting configuration for VR Recommender API.
Uses Flask-Limiter with in-memory storage (or Redis for production).
"""

import os
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_user_identifier():
    """
    Get rate limit key.
    Priority: user_id cookie > X-Forwarded-For > remote_addr
    """
    # Use user_id cookie if available (for returning users)
    user_id = request.cookies.get('user_id')
    if user_id:
        return f"user:{user_id}"

    # Use X-Forwarded-For if behind proxy
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"

    return f"ip:{get_remote_address()}"


def init_limiter(app):
    """
    Initialize rate limiter.
    Uses Redis in production, memory in development.
    """
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        storage_uri = redis_url
    else:
        # In-memory storage (not suitable for multi-process)
        storage_uri = "memory://"

    limiter = Limiter(
        app=app,
        key_func=get_user_identifier,
        storage_uri=storage_uri,
        default_limits=["200 per day", "50 per hour"],
        strategy="fixed-window",
        headers_enabled=True  # Add X-RateLimit headers
    )

    # Custom error handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        from src.audit_logger import log_security_event
        log_security_event("rate_limit_exceeded", "low", {
            "ip": request.remote_addr,
            "path": request.path
        })

        return jsonify({
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": e.description
        }), 429

    return limiter
```

#### Apply Rate Limits in `flask_api.py`

```python
from src.rate_limiter import init_limiter

app = Flask(__name__)
limiter = init_limiter(app)

# Chat endpoint - moderate limit
@app.route("/chat", methods=["GET", "POST"])
@limiter.limit("30 per minute")
@limiter.limit("200 per day")
def chat():
    # ... existing code ...

# Admin login - strict limit (prevent brute force)
@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@limiter.limit("20 per hour")
def admin_login():
    # ... existing code ...

# Data update - very strict (expensive operations)
@app.route("/api/admin/data/update/courses", methods=["POST"])
@admin_required
@limiter.limit("2 per hour")
def update_courses():
    # ... existing code ...

# Health check - no limit
@app.route("/health", methods=["GET"])
@limiter.exempt
def health():
    # ... existing code ...
```

---

## 3. CORS Configuration

Replace the open CORS configuration:

```python
# In flask_api.py, replace CORS(app) with:

from flask_cors import CORS

def configure_cors(app):
    """Configure CORS based on environment."""

    if os.getenv("FLASK_ENV") == "production":
        # Production: strict origins
        origins = [
            "https://your-domain.com",
            "https://www.your-domain.com",
        ]
    else:
        # Development: allow localhost
        origins = [
            "http://localhost:*",
            "http://127.0.0.1:*",
            "http://localhost:3000",  # React dev server
        ]

    CORS(app, resources={
        # Chat API - allow configured origins
        r"/chat": {
            "origins": origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True,
            "max_age": 3600
        },
        # Health check - allow any
        r"/health": {
            "origins": "*",
            "methods": ["GET"]
        },
        # Admin API - stricter
        r"/api/admin/*": {
            "origins": origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": True
        },
        # Embed widget - allow any (public widget)
        r"/chatbot_embed.js": {
            "origins": "*",
            "methods": ["GET"]
        }
    })

# Call after app creation
configure_cors(app)
```

---

## 4. Audit Logging

#### New File: `src/audit_logger.py`

```python
"""
Audit logging for admin operations and security events.
Logs to both file and MongoDB for persistence.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, has_request_context
from flask_login import current_user

# Configure file logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# File handler
import os
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(os.path.join(log_dir, 'audit.log'))
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(file_handler)


def log_admin_action(action: str, details: Dict[str, Any] = None):
    """
    Log an admin action for audit purposes.

    Args:
        action: Action type (e.g., 'login', 'logout', 'data_update')
        details: Additional context
    """
    user = "anonymous"
    if has_request_context():
        if hasattr(current_user, 'username'):
            user = current_user.username

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "admin_action",
        "user": user,
        "action": action,
        "ip": request.remote_addr if has_request_context() else None,
        "user_agent": request.user_agent.string if has_request_context() else None,
        "details": details or {}
    }

    # Log to file
    audit_logger.info(json.dumps(entry))

    # Log to MongoDB
    try:
        from src.db.mongo_connection import mongo
        mongo.get_collection('audit_logs').insert_one(entry)
    except Exception as e:
        audit_logger.error(f"Failed to log to MongoDB: {e}")


def log_security_event(
    event_type: str,
    severity: str,
    details: Dict[str, Any] = None
):
    """
    Log a security event.

    Args:
        event_type: Type (e.g., 'login_failed', 'rate_limit', 'suspicious')
        severity: 'low', 'medium', 'high', 'critical'
        details: Additional context
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "security_event",
        "event_type": event_type,
        "severity": severity,
        "ip": request.remote_addr if has_request_context() else None,
        "path": request.path if has_request_context() else None,
        "details": details or {}
    }

    # Use appropriate log level
    if severity in ('high', 'critical'):
        audit_logger.warning(json.dumps(entry))
    else:
        audit_logger.info(json.dumps(entry))

    # Log to MongoDB
    try:
        from src.db.mongo_connection import mongo
        mongo.get_collection('audit_logs').insert_one(entry)
    except Exception as e:
        audit_logger.error(f"Failed to log to MongoDB: {e}")


def get_audit_logs(
    limit: int = 100,
    event_type: Optional[str] = None,
    severity: Optional[str] = None
) -> list:
    """Retrieve audit logs from MongoDB."""
    try:
        from src.db.mongo_connection import mongo

        query = {}
        if event_type:
            query["event_type"] = event_type
        if severity:
            query["severity"] = severity

        return list(
            mongo.get_collection('audit_logs')
            .find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )
    except Exception:
        return []
```

---

## 5. Input Validation

#### New File: `src/validators.py`

```python
"""
Input validation and sanitization for API endpoints.
"""

import re
import html
from typing import Any, Dict

MAX_QUERY_LENGTH = 1000
MAX_MESSAGE_LENGTH = 2000

class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string input.
    - Trim whitespace
    - Limit length
    - Escape HTML entities
    - Remove null bytes
    """
    if not isinstance(value, str):
        raise ValidationError("Expected string input")

    # Remove null bytes
    cleaned = value.replace('\x00', '')

    # Trim whitespace
    cleaned = cleaned.strip()

    # Limit length
    cleaned = cleaned[:max_length]

    # Escape HTML entities
    cleaned = html.escape(cleaned)

    return cleaned


def validate_chat_message(message: Any) -> str:
    """Validate and sanitize chat message input."""
    if message is None:
        raise ValidationError("Message is required", "message")

    if not isinstance(message, str):
        raise ValidationError("Message must be a string", "message")

    sanitized = sanitize_string(message, MAX_MESSAGE_LENGTH)

    if len(sanitized) < 2:
        raise ValidationError("Message too short", "message")

    return sanitized


def validate_admin_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate admin API parameters."""
    validated = {}

    # Validate limit
    if 'limit' in params and params['limit'] is not None:
        try:
            limit = int(params['limit'])
            if limit < 1 or limit > 1000:
                raise ValidationError("Limit must be between 1 and 1000", "limit")
            validated['limit'] = limit
        except (ValueError, TypeError):
            raise ValidationError("Limit must be a number", "limit")

    # Validate offset
    if 'offset' in params and params['offset'] is not None:
        try:
            offset = int(params['offset'])
            if offset < 0:
                raise ValidationError("Offset must be non-negative", "offset")
            validated['offset'] = offset
        except (ValueError, TypeError):
            raise ValidationError("Offset must be a number", "offset")

    # Validate user_id (UUID format)
    if 'user_id' in params and params['user_id']:
        user_id = str(params['user_id'])
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(user_id):
            raise ValidationError("Invalid user_id format", "user_id")
        validated['user_id'] = user_id

    return validated
```

#### Apply Validation in `flask_api.py`

```python
from src.validators import validate_chat_message, validate_admin_params, ValidationError

@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({
        "error": "Validation error",
        "message": e.message,
        "field": e.field
    }), 400


@app.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = validate_chat_message(data.get("message"))
        # ... continue with validated message
    except ValidationError as e:
        return jsonify({
            "error": e.message,
            "field": e.field
        }), 400


@app.route("/api/admin/logs", methods=["GET"])
@admin_required
def admin_logs():
    try:
        params = validate_admin_params({
            'limit': request.args.get('limit', 50),
            'offset': request.args.get('offset', 0),
            'user_id': request.args.get('user_id')
        })
        # ... continue with validated params
    except ValidationError as e:
        return jsonify({"error": e.message}), 400
```

---

## 6. Enhanced Health Check

```python
@app.route("/health", methods=["GET"])
@limiter.exempt
def health():
    """
    Enhanced health check with dependency status.
    Returns 200 if healthy, 503 if degraded.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("FLASK_ENV", "development"),
        "checks": {}
    }

    # Check MongoDB
    try:
        from src.db.mongo_connection import mongo
        mongo._client.admin.command('ping')
        health_status["checks"]["mongodb"] = "ok"
    except Exception as e:
        health_status["checks"]["mongodb"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"

    # Check Neo4j
    try:
        from knowledge_graph.src.knowledge_graph.connection import Neo4jConnection
        neo4j = Neo4jConnection()
        if neo4j.test_connection():
            health_status["checks"]["neo4j"] = "ok"
        else:
            health_status["checks"]["neo4j"] = "connection failed"
            health_status["status"] = "degraded"
        neo4j.close()
    except Exception as e:
        health_status["checks"]["neo4j"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"

    # Check recommender
    health_status["checks"]["recommender"] = "ok" if recommender else "unavailable"
    if not recommender:
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code
```

---

## 7. Secrets Management

### Environment Variables Structure

```bash
# .env.example

# ===========================================
# REQUIRED - Application will not start without these
# ===========================================

# Flask
FLASK_SECRET_KEY=          # python -c "import secrets; print(secrets.token_hex(32))"
FLASK_ENV=production       # production | development

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=       # Generate with: python scripts/generate_admin_password.py

# LLM API
OPENROUTER_API_KEY=        # Your OpenRouter API key

# ===========================================
# OPTIONAL - Defaults provided
# ===========================================

# MongoDB
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=vr_recommender

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password    # Change in production!

# OpenRouter
OPENROUTER_MODEL=google/gemini-2.0-flash-001

# Data Collection (optional)
FIRECRAWL_API_KEY=
TAVILY_API_KEY=

# Redis (optional, for distributed rate limiting)
REDIS_URL=
```

### Docker Secrets Injection

```yaml
# docker-compose.prod.yml
services:
  flask-api:
    env_file:
      - .env.production
    # Or use Docker secrets
    secrets:
      - openrouter_api_key
      - admin_password_hash

secrets:
  openrouter_api_key:
    file: ./secrets/openrouter_api_key.txt
  admin_password_hash:
    file: ./secrets/admin_password_hash.txt
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/auth.py` | Admin authentication |
| `src/rate_limiter.py` | Rate limiting configuration |
| `src/audit_logger.py` | Audit logging |
| `src/validators.py` | Input validation |
| `templates/admin_login.html` | Login page |
| `scripts/generate_admin_password.py` | Password hash generator |
| `.env.example` | Environment template |

## Files to Modify

| File | Changes |
|------|---------|
| `flask_api.py` | Add auth, rate limiting, CORS, validation |
| `requirements.txt` | Add security packages |

## Dependencies to Add

```txt
# requirements.txt additions
flask-login==0.6.3
bcrypt==4.1.2
flask-limiter==3.5.0
redis==5.0.1  # Optional, for distributed rate limiting
```

---

## Testing Checklist

- [ ] Admin login page loads correctly
- [ ] Invalid credentials show error message
- [ ] Valid credentials allow access to /admin
- [ ] /admin routes redirect to login when not authenticated
- [ ] /api/admin/* returns 401 when not authenticated
- [ ] Logout clears session
- [ ] Rate limiting blocks excessive requests
- [ ] Rate limit headers are present in responses
- [ ] CORS blocks unauthorized origins
- [ ] CORS allows configured origins
- [ ] Input validation rejects malformed data
- [ ] Audit logs are written for admin actions
- [ ] Security events are logged
- [ ] Health check includes all dependencies
- [ ] Password hash generation script works

---

## Security Testing Commands

```bash
# Test rate limiting
for i in {1..35}; do curl -s http://localhost:5000/chat -X POST -H "Content-Type: application/json" -d '{"message":"test"}' | head -c 100; echo; done

# Test admin authentication
curl -c cookies.txt -b cookies.txt http://localhost:5000/admin/login -X POST -d "username=admin&password=wrongpass"
curl -c cookies.txt -b cookies.txt http://localhost:5000/admin/login -X POST -d "username=admin&password=correctpass"
curl -b cookies.txt http://localhost:5000/admin

# Test CORS
curl -H "Origin: http://evil.com" http://localhost:5000/chat -X OPTIONS -v

# View audit logs
docker-compose exec flask-api tail -f /app/logs/audit.log
```
