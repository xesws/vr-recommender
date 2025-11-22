#!/bin/bash
# 停止所有 VR Recommender 服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "         VR Recommender - 停止所有服务"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# 停止 Flask API
log_info "停止 Flask API..."
if [ -f "flask_api.pid" ]; then
    pid=$(cat flask_api.pid)
    if ps -p $pid > /dev/null 2>&1; then
        kill $pid
        log_success "Flask API (PID: $pid) 已停止"
    else
        log_info "Flask API 进程不存在"
    fi
    rm -f flask_api.pid
fi

# 强制清理端口 5000 和 5001
for port in 5000 5001; do
    if lsof -ti:$port >/dev/null 2>&1; then
        log_info "清理端口 $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        log_success "端口 $port 已清理"
    fi
done

# 停止 Neo4j
if command -v neo4j &> /dev/null; then
    log_info "停止 Neo4j..."
    neo4j stop >/dev/null 2>&1 || true
    log_success "Neo4j 已停止"
fi

# 清理端口 7687
if lsof -ti:7687 >/dev/null 2>&1; then
    log_info "清理 Neo4j 端口..."
    lsof -ti:7687 | xargs kill -9 2>/dev/null || true
    log_success "Neo4j 端口已清理"
fi

# 清理其他进程
pkill -f "python.*flask_api.py" 2>/dev/null || true
pkill -f "python.*http.server" 2>/dev/null || true

echo ""
log_success "所有服务已停止！"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
