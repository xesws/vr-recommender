#!/bin/bash
# VR Recommender Project - All-in-One Startup Script
# Automatically checks, installs (if needed), and starts all dependency services.

set -e  # Exit on any error

# Color Definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper Functions ---

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_port() {
    local port=$1
    if nc -z localhost $port 2>/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

kill_port() {
    local port=$1
    log_warning "Port $port is in use, cleaning up..."

    local pid=$(lsof -ti:$port 2>/dev/null || true)

    if [ -n "$pid" ]; then
        log_info "Killing process PID: $pid"
        kill -9 $pid 2>/dev/null || true
        sleep 2

        if check_port $port; then
            log_error "Failed to release port $port"
            return 1
        fi
    fi

    log_success "Port $port released"
    return 0
}

# --- Service Management Functions ---

start_neo4j() {
    log_info "Checking Neo4j service..."

    if check_port 7687; then
        log_success "Neo4j is running (Port 7687)"
        return 0
    fi

    log_info "Starting Neo4j..."
    if ! command -v neo4j &> /dev/null; then
        log_error "Neo4j not found! Please install Neo4j."
        return 1
    fi

    neo4j start 2>/dev/null || log_warning "Neo4j might be starting or already running"

    # Wait for startup
    local retries=30
    while [ $retries -gt 0 ]; do
        if check_port 7687; then
            log_success "Neo4j started successfully (Port 7687)"
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done

    log_error "Neo4j startup timed out"
    return 1
}

start_mongodb() {
    log_info "Checking MongoDB service..."

    if pgrep -x "mongod" > /dev/null; then
        log_success "MongoDB is running"
        return 0
    fi

    log_info "Starting MongoDB..."
    if ! command -v mongod &> /dev/null; then
        log_warning "MongoDB not found. Attempting to install via Homebrew..."
        if command -v brew &> /dev/null; then
            brew tap mongodb/brew
            brew install mongodb-community
            log_success "MongoDB installed"
        else
            log_error "Homebrew not found. Please install MongoDB manually."
            return 1
        fi
    fi

    # Start service
    if command -v brew &> /dev/null; then
        brew services start mongodb/brew/mongodb-community
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start mongod
    else
        # Fallback for manual start
        mongod --fork --logpath /tmp/mongod.log
    fi

    sleep 3
    if pgrep -x "mongod" > /dev/null; then
        log_success "MongoDB started successfully"
        return 0
    else
        log_error "Failed to start MongoDB"
        return 1
    fi
}

install_dependencies() {
    if [ ! -d "venv" ] && [ -f "requirements.txt" ]; then
        log_info "Checking python dependencies..."
        # Simple check if flask is installed
        if ! python3 -c "import flask" 2>/dev/null; then
            log_warning "Dependencies missing. Installing from requirements.txt..."
            pip install -r requirements.txt
            log_success "Dependencies installed"
        fi
    fi
}

cleanup_flask() {
    log_info "Checking for existing Flask API processes..."
    local pids=$(ps aux | grep 'web/flask_api.py' | grep -v grep | awk '{print $2}' || true)

    if [ -n "$pids" ]; then
        log_warning "Found existing Flask process, cleaning up..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 2
        log_success "Flask process cleaned"
    else
        log_success "No existing Flask process found"
    fi

    for port in 5000 5001; do
        if check_port $port; then
            kill_port $port
        fi
    done
}

start_flask() {
    local port=$1
    local background=$2
    log_info "Starting Flask API on port $port..."

    if [ -z "$VIRTUAL_ENV" ]; then
        log_warning "No virtual environment detected. Recommended to run in venv."
    fi

    export PYTHONPATH="$(pwd):$(pwd)/stage3:$(pwd)/stage4"
    export PORT=$port

    # Create logs dir if not exists
    mkdir -p logs

    # Start in background using nohup
    # We use flask_api.pid to track the process ID
    nohup python web/flask_api.py > logs/flask_${port}.log 2>&1 &
    local flask_pid=$!
    echo $flask_pid > flask_api.pid

    log_info "Flask API PID: $flask_pid"

    # Wait for health check
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:$port/health >/dev/null 2>&1; then
            log_success "Flask API started successfully (http://localhost:$port)"
            echo ""
            echo "╔══════════════════════════════════════════════════════════════════╗"
            echo "║                    🚀 PROJECT STARTED!                            ║"
            echo "╚══════════════════════════════════════════════════════════════════╝"
            echo ""
            echo "📍 Access Points:"
            echo "   GET  http://localhost:$port/          → Chatbot Interface"
            echo "   POST http://localhost:$port/chat      → Get Recommendations"
            echo "   GET  http://localhost:$port/health    → Health Check"
            echo ""
            
            if [ "$background" == "true" ]; then
                log_success "Running in background. Use './stop_all.sh' to stop."
            fi
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done

    log_error "Flask API failed to start."
    log_info "Check log: logs/flask_${port}.log"
    return 1
}

# --- Main Execution ---

main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║         VR Recommender System - Startup Script                    ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""

    local port=${1:-5000}
    local background="false"
    
    # Handle arguments
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --background|-d) background="true" ;;
            --force) ;; # Handled by wrapper but good to ignore here
            [0-9]*) port=$1 ;; # Port number
            *) echo "Unknown parameter passed: $1"; exit 1 ;;
        esac
        shift
    done

    # 1. Dependencies
    install_dependencies

    # 2. Databases
    if ! start_neo4j; then
        log_error "Neo4j check failed, continuing anyway..."
    fi
    
    if ! start_mongodb; then
        log_error "MongoDB check failed, continuing anyway..."
    fi
    echo ""

    # 3. Cleanup
    cleanup_flask
    echo ""

    # 4. Start App
    if start_flask $port $background; then
        echo "📝 Log file:"
        echo "   logs/flask_${port}.log"
        
        if [ "$background" == "false" ]; then
            echo ""
            echo "💡 Tip: Press Ctrl+C to stop following the log (server stays running)"
            echo "═══════════════════════════════════════════════════════════════════"
            tail -f logs/flask_${port}.log 2>/dev/null || true
        fi
    else
        exit 1
    fi
}

# Help
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [PORT] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  PORT             Flask API port (default: 5000)"
    echo "  --background, -d Start in background (daemon mode)"
    echo "  --force          Force restart all services"
    echo ""
    exit 0
fi

# Handle force restart wrapper
if [ "$1" == "--force" ]; then
    # Stop everything first if force is requested
    ./stop_all.sh
    sleep 2
    shift # remove --force
    main "$@"
else
    main "$@"
fi