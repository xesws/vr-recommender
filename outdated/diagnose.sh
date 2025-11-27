#!/bin/bash
# 一键诊断脚本 - 检查所有可能的问题

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              VR Recommender - 系统诊断工具                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查函数
check_service() {
    local name=$1
    local command=$2

    echo -n "  $name: "
    if eval $command >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 异常${NC}"
        return 1
    fi
}

echo "1️⃣  检查服务状态"
echo "═══════════════════════════════════════════════════════════════════"
check_service "Neo4j (7687)" "nc -z localhost 7687"
check_service "Neo4j Web (7474)" "curl -s http://localhost:7474 >/dev/null"
check_service "Flask API (5000)" "curl -s http://localhost:5000/health >/dev/null"
check_service "Flask API (5001)" "curl -s http://localhost:5001/health >/dev/null"
echo ""

echo "2️⃣  检查端口占用"
echo "═══════════════════════════════════════════════════════════════════"
for port in 5000 5001 7474 7687; do
    echo -n "  端口 $port: "
    if nc -z localhost $port 2>/dev/null; then
        pid=$(lsof -ti:$port 2>/dev/null | head -1 || echo "unknown")
        echo -e "${GREEN}✓ 被占用 (PID: $pid)${NC}"
    else
        echo -e "${YELLOW}⚠ 未使用${NC}"
    fi
done
echo ""

echo "3️⃣  测试 API 响应"
echo "═══════════════════════════════════════════════════════════════════"

# 测试 Flask API
if curl -s http://localhost:5001/health >/dev/null 2>&1; then
    echo "  Flask API 响应:"
    curl -s http://localhost:5001/health | python3 -m json.tool 2>/dev/null | head -5
else
    echo -e "  ${RED}Flask API 无响应${NC}"
fi
echo ""

echo "4️⃣  Python 环境"
echo "═══════════════════════════════════════════════════════════════════"
echo "  Python 版本: $(python3 --version)"
echo "  虚拟环境: ${VIRTUAL_ENV:-未激活}"
echo "  当前目录: $(pwd)"
echo ""

echo "5️⃣  进程信息"
echo "═══════════════════════════════════════════════════════════════════"
echo "  Flask 进程:"
ps aux | grep -E "flask_api|python.*5001" | grep -v grep | while read line; do
    echo "    $line"
done
echo ""

echo "6️⃣  建议的访问地址"
echo "═══════════════════════════════════════════════════════════════════"
echo "  • 测试页面:  http://127.0.0.1:8000/test_access.html"
echo "  • Chatbot:   http://127.0.0.1:5001"
echo "  • 健康检查:  http://127.0.0.1:5001/health"
echo "  • Neo4j UI:  http://127.0.0.1:7474"
echo ""

echo "7️⃣  如果遇到问题，尝试这些命令"
echo "═══════════════════════════════════════════════════════════════════"
echo "  重启服务:   ./restart.sh"
echo "  启动服务:   ./start_services.sh"
echo "  停止服务:   ./stop_all.sh"
echo "  查看状态:   ./status.sh"
echo ""

echo "═══════════════════════════════════════════════════════════════════"
echo ""
