# Stage 17: Docker Containerization and AWS EC2 Deployment

## Overview

Containerize the VR Recommender application using Docker and deploy to a single AWS EC2 instance with all services.

**Status**: Planned
**Priority**: High
**Estimated Duration**: 1 week
**Dependencies**: Stage 16 (MongoDB migration) must be complete

---

## Architecture

### Budget-Optimized Single EC2 Deployment (~$60/month)

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                 AWS EC2 (t3.large)                       │
│                 2 vCPU, 8GB RAM                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Docker Compose Stack                   │ │
│  │                                                     │ │
│  │  ┌─────────────┐     ┌─────────────┐              │ │
│  │  │   Nginx     │     │   Flask     │              │ │
│  │  │   :80/443   │────▶│   Gunicorn  │              │ │
│  │  │   (SSL)     │     │   :5000     │              │ │
│  │  └─────────────┘     └──────┬──────┘              │ │
│  │                              │                     │ │
│  │         ┌────────────────────┼────────────────┐   │ │
│  │         │                    │                │   │ │
│  │         ▼                    ▼                ▼   │ │
│  │  ┌─────────────┐     ┌─────────────┐  ┌──────────┐│ │
│  │  │  MongoDB    │     │   Neo4j     │  │ ChromaDB ││ │
│  │  │  :27017     │     │   :7687     │  │ (in-app) ││ │
│  │  └─────────────┘     └─────────────┘  └──────────┘│ │
│  │                                                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  EBS gp3 50GB (Persistent Data Volumes)                 │
│    ├── /data/mongodb                                     │
│    ├── /data/neo4j                                       │
│    └── /data/chroma                                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Docker Configuration

### Project Structure

```
vr-recommender/
├── Dockerfile                 # Flask application
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production overrides
├── nginx/
│   ├── nginx.conf            # Nginx configuration
│   └── ssl/                  # SSL certificates (gitignored)
├── scripts/
│   ├── deploy.sh             # Deployment script
│   ├── backup.sh             # Data backup script
│   └── healthcheck.sh        # Health check script
└── .dockerignore
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data
RUN mkdir -p /app/vector_store/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "flask_api:app"]
```

### docker-compose.yml (Development)

```yaml
version: '3.8'

services:
  flask-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: vr-flask
    ports:
      - "5000:5000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/
      - MONGODB_DB=vr_recommender
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL:-google/gemini-2.0-flash-001}
      - CHROMA_PERSIST_DIR=/app/vector_store/data/chroma
    volumes:
      - chroma_data:/app/vector_store/data
      - logs:/app/logs
    depends_on:
      mongodb:
        condition: service_healthy
      neo4j:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - vr-network

  mongodb:
    image: mongo:7.0
    container_name: vr-mongodb
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - vr-network

  neo4j:
    image: neo4j:5.15-community
    container_name: vr-neo4j
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-password}
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=256M
      - NEO4J_dbms_memory_heap_max__size=512M
      - NEO4J_dbms_memory_pagecache_size=256M
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - vr-network

volumes:
  mongo_data:
  neo4j_data:
  neo4j_logs:
  chroma_data:
  logs:

networks:
  vr-network:
    driver: bridge
```

### docker-compose.prod.yml (Production Overrides)

```yaml
version: '3.8'

services:
  flask-api:
    environment:
      - FLASK_ENV=production
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  mongodb:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  neo4j:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  nginx:
    image: nginx:alpine
    container_name: vr-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - logs:/var/log/nginx
    depends_on:
      - flask-api
    restart: unless-stopped
    networks:
      - vr-network
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream flask {
        server flask-api:5000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/s;

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000" always;

        # API endpoints
        location /chat {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://flask;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 120s;
        }

        # Health check (no rate limit)
        location /health {
            proxy_pass http://flask;
        }

        # Admin endpoints (stricter rate limit)
        location /admin {
            limit_req zone=admin burst=10 nodelay;
            proxy_pass http://flask;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/admin {
            limit_req zone=admin burst=10 nodelay;
            proxy_pass http://flask;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files and chatbot embed
        location / {
            proxy_pass http://flask;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### .dockerignore

```
# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
.venv/
*.egg-info/
.eggs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Local data (will use volumes)
*.db
*.sqlite
vr_recommender.db
vector_store/data/
logs/
chat_logs/

# Environment
.env
.env.local
.env.production

# Documentation
*.md
stage-dev/

# Misc
.DS_Store
Thumbs.db
```

---

## AWS EC2 Deployment

### Step 1: Create EC2 Instance

**AWS Console Configuration:**

| Setting | Value |
|---------|-------|
| AMI | Amazon Linux 2023 |
| Instance Type | t3.large (2 vCPU, 8GB) |
| Storage | 50GB gp3 |
| Security Group | See below |
| Key Pair | Create new or use existing |

**Security Group Rules:**

| Type | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | Your IP | Admin access |
| HTTP | 80 | 0.0.0.0/0 | Web (redirects to HTTPS) |
| HTTPS | 443 | 0.0.0.0/0 | Web secure |

### Step 2: Install Docker on EC2

```bash
#!/bin/bash
# scripts/setup-ec2.sh

# Update system
sudo dnf update -y

# Install Docker
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo dnf install git -y

# Create app directory
sudo mkdir -p /opt/vr-recommender
sudo chown ec2-user:ec2-user /opt/vr-recommender

echo "Setup complete! Log out and back in for docker group to take effect."
```

### Step 3: Deploy Application

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

APP_DIR="/opt/vr-recommender"
REPO_URL="https://github.com/your-org/vr-recommender.git"

echo "=== VR Recommender Deployment ==="

# Clone or pull latest
if [ -d "$APP_DIR/.git" ]; then
    echo "Pulling latest changes..."
    cd $APP_DIR
    git pull origin main
else
    echo "Cloning repository..."
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Copy environment file
if [ ! -f "$APP_DIR/.env" ]; then
    echo "ERROR: .env file not found. Please create it first."
    exit 1
fi

# Build and start containers
echo "Building containers..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "Starting containers..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Run migrations if needed
echo "Running data migrations..."
docker-compose exec flask-api python scripts/migrate_to_mongodb.py

# Verify deployment
echo "Verifying deployment..."
curl -s http://localhost:5000/health | python3 -m json.tool

echo "=== Deployment Complete ==="
docker-compose ps
```

### Step 4: SSL Certificate Setup (Let's Encrypt)

```bash
#!/bin/bash
# scripts/setup-ssl.sh

DOMAIN="your-domain.com"

# Install Certbot
sudo dnf install certbot -y

# Stop nginx temporarily
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

# Copy certificates to nginx ssl directory
sudo mkdir -p /opt/vr-recommender/nginx/ssl
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/vr-recommender/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/vr-recommender/nginx/ssl/
sudo chown -R ec2-user:ec2-user /opt/vr-recommender/nginx/ssl

# Restart nginx
docker-compose start nginx

# Setup auto-renewal cron
echo "0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/*.pem /opt/vr-recommender/nginx/ssl/ && docker-compose restart nginx" | sudo crontab -

echo "SSL setup complete for $DOMAIN"
```

### Step 5: Data Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="your-backup-bucket"

mkdir -p $BACKUP_DIR

echo "=== Starting Backup ==="

# Backup MongoDB
echo "Backing up MongoDB..."
docker-compose exec -T mongodb mongodump --archive > $BACKUP_DIR/mongodb_$DATE.archive

# Backup Neo4j
echo "Backing up Neo4j..."
docker-compose exec -T neo4j neo4j-admin database dump neo4j --to-stdout > $BACKUP_DIR/neo4j_$DATE.dump

# Backup ChromaDB (copy volume)
echo "Backing up ChromaDB..."
docker run --rm -v vr-recommender_chroma_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/chroma_$DATE.tar.gz /data

# Upload to S3 (optional)
if command -v aws &> /dev/null; then
    echo "Uploading to S3..."
    aws s3 cp $BACKUP_DIR/mongodb_$DATE.archive s3://$S3_BUCKET/mongodb/
    aws s3 cp $BACKUP_DIR/neo4j_$DATE.dump s3://$S3_BUCKET/neo4j/
    aws s3 cp $BACKUP_DIR/chroma_$DATE.tar.gz s3://$S3_BUCKET/chroma/
fi

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -mtime +7 -delete

echo "=== Backup Complete ==="
ls -la $BACKUP_DIR
```

---

## Environment Variables

### .env.example

```bash
# ===========================================
# VR Recommender Environment Configuration
# ===========================================
# Copy this file to .env and fill in values

# Flask
FLASK_ENV=production
FLASK_SECRET_KEY=  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

# MongoDB
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=vr_recommender

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=  # Set a strong password

# OpenRouter (LLM API)
OPENROUTER_API_KEY=  # Your API key
OPENROUTER_MODEL=google/gemini-2.0-flash-001

# ChromaDB
CHROMA_PERSIST_DIR=/app/vector_store/data/chroma

# Admin (Stage 18)
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=  # Generate with scripts/generate_admin_password.py

# Data Collection APIs (optional)
FIRECRAWL_API_KEY=
TAVILY_API_KEY=
```

---

## Performance Tuning for 200+ Concurrent Users

### Gunicorn Configuration

```python
# gunicorn.conf.py
import multiprocessing

# Workers = 2-4 x CPU cores
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = 'gthread'

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = '/app/logs/access.log'
errorlog = '/app/logs/error.log'
loglevel = 'info'

# Performance
max_requests = 1000
max_requests_jitter = 50
```

### MongoDB Connection Pool

```python
# Already configured in mongo_connection.py
MongoClient(
    uri,
    maxPoolSize=50,      # Max connections
    minPoolSize=10,      # Min connections
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000
)
```

### Neo4j Connection Pool

```python
# Update connection.py
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    uri,
    auth=(user, password),
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

---

## Cost Breakdown

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| EC2 t3.large | 2 vCPU, 8GB RAM (1yr Reserved) | ~$45 |
| EBS gp3 | 50GB | ~$5 |
| Data Transfer | ~50GB/month outbound | ~$5 |
| Elastic IP | 1 | ~$4 |
| Route 53 | 1 hosted zone (optional) | ~$0.50 |
| **Total** | | **~$60/month** |

**Cost Optimization Tips:**
- Use 1-year Reserved Instance for 30-40% savings
- Enable EC2 instance stop/start scheduling for non-peak hours
- Use S3 Glacier for old backups

---

## Files to Create

| File | Purpose |
|------|---------|
| `Dockerfile` | Flask application container |
| `docker-compose.yml` | Development stack |
| `docker-compose.prod.yml` | Production overrides |
| `nginx/nginx.conf` | Reverse proxy config |
| `.dockerignore` | Build exclusions |
| `gunicorn.conf.py` | Gunicorn settings |
| `scripts/setup-ec2.sh` | EC2 initial setup |
| `scripts/deploy.sh` | Deployment automation |
| `scripts/backup.sh` | Data backup |
| `scripts/setup-ssl.sh` | SSL certificate setup |
| `.env.example` | Environment template |

---

## Testing Checklist

- [ ] Docker build completes without errors
- [ ] docker-compose up starts all services
- [ ] Health check returns healthy status
- [ ] MongoDB connection works from Flask
- [ ] Neo4j connection works from Flask
- [ ] ChromaDB vector search works
- [ ] Nginx proxies requests correctly
- [ ] SSL certificate is valid
- [ ] 200 concurrent users load test passes
- [ ] Backup script runs successfully
- [ ] Data persists across container restarts

---

## Monitoring Commands

```bash
# View all container status
docker-compose ps

# View logs
docker-compose logs -f flask-api
docker-compose logs -f nginx

# Resource usage
docker stats

# Health check
curl https://your-domain.com/health

# MongoDB status
docker-compose exec mongodb mongosh --eval "db.serverStatus()"

# Neo4j status
docker-compose exec neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "CALL dbms.components()"
```
