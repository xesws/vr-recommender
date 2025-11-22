#!/bin/bash
# 后台启动所有服务 (非阻塞)

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# 创建日志目录
mkdir -p logs

# 检查并清理端口
check_and_kill_port() {
    local port=$1
    local service_name=$2

    if lsof -ti:$port >/dev/null 2>&1; then
        log_info "端口 $port 被占用，清理 $service_name..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# 启动服务函数
start_service() {
    local service_name=$1
    local command=$2
    local log_file=$3

    log_info "启动 $service_name..."

    # 在后台运行服务
    nohup $command > $log_file 2>&1 &
    local pid=$!
    echo $pid > ${service_name}.pid

    log_success "$service_name 已启动 (PID: $pid)"
    echo "   日志: $log_file"
    echo "   PID 文件: ${service_name}.pid"
}

# 主启动流程
main() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "         VR Recommender - 后台服务启动器"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""

    # 1. 清理现有进程
    log_info "清理现有进程..."
    check_and_kill_port 7687 "Neo4j"
    check_and_kill_port 5000 "Flask API"
    check_and_kill_port 5001 "Flask API"
    echo ""

    # 2. 启动 Neo4j
    if command -v neo4j &> /dev/null; then
        log_info "启动 Neo4j..."
        neo4j start >/dev/null 2>&1

        # 等待 Neo4j 启动
        local retries=30
        while [ $retries -gt 0 ]; do
            if nc -z localhost 7687 2>/dev/null; then
                log_success "Neo4j 已就绪"
                break
            fi
            sleep 1
            retries=$((retries - 1))
        done
    else
        echo "⚠️  Neo4j 未安装，跳过"
    fi
    echo ""

    # 3. 设置 Python 环境
    export PYTHONPATH="$(pwd):$(pwd)/stage3:$(pwd)/stage4"

    # 4. 启动 Flask API (在端口 5001)
    log_info "启动 Flask API on 端口 5001..."
    nohup python flask_api.py > logs/flask_api.log 2>&1 &
    local flask_pid=$!
    echo $flask_pid > flask_api.pid
    echo ""

    # 等待 Flask 启动
    log_info "等待 Flask API 就绪..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:5001/health >/dev/null 2>&1; then
            log_success "Flask API 就绪 (http://localhost:5001)"
            break
        fi
        sleep 1
        retries=$((retries - 1))
    done

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    log_success "所有服务已在后台启动！"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "📍 访问地址:"
    echo "   Flask API: http://localhost:5001"
    echo "   Neo4j UI:  http://localhost:7474"
    echo ""
    echo "📝 日志文件:"
    echo "   logs/flask_api.log"
    echo ""
    echo "🔧 管理命令:"
    echo "   停止所有: ./stop_all.sh"
    echo "   查看状态: ./status.sh"
    echo "   查看日志: tail -f logs/flask_api.log"
    echo ""
}

main "$@"
