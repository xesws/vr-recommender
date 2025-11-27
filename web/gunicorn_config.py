import multiprocessing
import os

# Gunicorn Configuration

# Bind to all interfaces on port 5001 (To avoid conflict with AirPlay on 5000)
bind = "0.0.0.0:5000"

# Worker configuration
# For CPU-bound tasks: workers = 2 * CPUs + 1
# For I/O-bound tasks (like LLM calls), we need more threads per worker
workers = 4
threads = 4  # Allow each worker to handle multiple concurrent requests
worker_class = "gthread" # Use threaded workers

# Timeouts
# LLMs can be slow, so we need a generous timeout
timeout = 120 
keepalive = 5

# Logging
accesslog = "-" # Stdout
errorlog = "-"  # Stderr
loglevel = "info"

# Development reload (turn off in production usually, but useful for now)
reload = False

# App module
wsgi_app = "flask_api:app"

# Environment
raw_env = [
    "FLASK_ENV=production"
]