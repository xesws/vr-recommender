#!/bin/bash
# VR Recommender Project - 一键启动脚本
# 自动检查并启动所有依赖服务

set -e  # Exit on any error

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查端口是否被占用
check_port() {
    local port=$1
    if nc -z localhost $port 2>/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# 终止端口上的进程
kill_port() {
    local port=$1
    log_warning "端口 $port 被占用，正在清理..."

    # 获取占用端口的进程 PID
    local pid=$(lsof -ti:$port 2>/dev/null || true)

    if [ -n "$pid" ]; then
        log_info "终止进程 PID: $pid"
        kill -9 $pid 2>/dev/null || true
        sleep 2

        # 验证端口已被释放
        if check_port $port; then
            log_error "无法释放端口 $port"
            return 1
        fi
    fi

    log_success "端口 $port 已释放"
    return 0
}

# 启动 Neo4j
start_neo4j() {
    log_info "检查 Neo4j 服务..."

    if check_port 7687; then
        log_success "Neo4j 已在运行 (端口 7687)"
        return 0
    fi

    log_info "启动 Neo4j..."
    # 检查 Neo4j 是否安装
    if ! command -v neo4j &> /dev/null; then
        log_error "Neo4j 未安装！请先安装 Neo4j"
        return 1
    fi

    # 启动 Neo4j (后台运行)
    neo4j start 2>/dev/null || log_warning "Neo4j 可能已在运行"

    # 等待 Neo4j 启动
    local retries=30
    while [ $retries -gt 0 ]; do
        if check_port 7687; then
            log_success "Neo4j 启动成功 (端口 7687)"
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done

    log_error "Neo4j 启动超时"
    return 1
}

# 清理 Flask 进程
cleanup_flask() {
    log_info "检查 Flask API 进程..."

    # 查找并终止所有 flask_api.py 进程
    local pids=$(ps aux | grep 'flask_api.py' | grep -v grep | awk '{print $2}' || true)

    if [ -n "$pids" ]; then
        log_warning "发现 Flask API 进程，正在清理..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 2
        log_success "Flask API 进程已清理"
    else
        log_success "没有发现 Flask API 进程"
    fi

    # 清理端口 5000 和 5001
    for port in 5000 5001; do
        if check_port $port; then
            kill_port $port
        fi
    done
}

# 启动 Flask API
start_flask() {
    local port=$1
    log_info "启动 Flask API on 端口 $port..."

    # 检查虚拟环境
    if [ -z "$VIRTUAL_ENV" ]; then
        log_warning "未检测到虚拟环境，建议在虚拟环境中运行"
    fi

    # 导出环境变量
    export PYTHONPATH="$(pwd):$(pwd)/stage3:$(pwd)/stage4"
    export PORT=$port

    # 启动 Flask (后台运行)
    python flask_api.py > flask_${port}.log 2>&1 &
    local flask_pid=$!

    log_info "Flask API PID: $flask_pid"

    # 等待 Flask 启动
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:$port/health >/dev/null 2>&1; then
            log_success "Flask API 启动成功 (http://localhost:$port)"
            echo ""
            echo "╔══════════════════════════════════════════════════════════════════╗"
            echo "║                    🚀 项目启动成功!                               ║"
            echo "╚══════════════════════════════════════════════════════════════════╝"
            echo ""
            echo "📍 可用端点:"
            echo "   GET  http://localhost:$port/          → Chatbot 界面"
            echo "   POST http://localhost:$port/chat      → 获取推荐"
            echo "   GET  http://localhost:$port/health    → 健康检查"
            echo ""
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done

    log_error "Flask API 启动失败"
    log_info "查看日志: flask_${port}.log"
    return 1
}

# 主函数
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║         VR Recommender Project - 一键启动脚本                     ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""

    # 解析命令行参数
    local port=${1:-5000}
    local force_restart=${2:-false}

    # 如果不是强制重启，先检查服务是否已运行
    if [ "$force_restart" != "true" ]; then
        if curl -s http://localhost:$port/health >/dev/null 2>&1; then
            log_success "Flask API 已在端口 $port 运行"
            echo "   访问: http://localhost:$port"
            return 0
        fi
    fi

    # 步骤 1: 启动 Neo4j
    if ! start_neo4j; then
        log_error "Neo4j 启动失败，尝试继续..."
    fi
    echo ""

    # 步骤 2: 清理现有 Flask 进程
    cleanup_flask
    echo ""

    # 步骤 3: 启动 Flask API
    if start_flask $port; then
        # 显示日志位置
        echo "📝 日志文件:"
        echo "   flask_${port}.log"
        echo ""
        echo "💡 提示: 使用 Ctrl+C 停止服务"
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"

        # 保持脚本运行并显示日志
        tail -f flask_${port}.log 2>/dev/null || true
    else
        exit 1
    fi
}

# 显示帮助
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "用法: $0 [端口号] [选项]"
    echo ""
    echo "参数:"
    echo "  端口号     Flask API 端口 (默认: 5000)"
    echo "  --force    强制重启所有服务"
    echo ""
    echo "示例:"
    echo "  $0              # 在端口 5000 启动"
    echo "  $0 5001         # 在端口 5001 启动"
    echo "  $0 --force      # 强制重启所有服务"
    echo ""
    exit 0
fi

# 强制重启参数
if [ "$1" == "--force" ]; then
    main 5000 true
else
    main "$@"
fi
