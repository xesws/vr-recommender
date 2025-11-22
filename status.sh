#!/bin/bash
# 检查所有服务状态

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_service() {
    local name=$1
    local port=$2
    local url=$3

    echo -n "  $name: "

    if [ -n "$url" ]; then
        # HTTP 检查
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ 运行中${NC} ($port)"
        else
            echo -e "${RED}✗ 未运行${NC} ($port)"
        fi
    else
        # 端口检查
        if nc -z localhost $port 2>/dev/null; then
            echo -e "${GREEN}✓ 运行中${NC} ($port)"
        else
            echo -e "${RED}✗ 未运行${NC} ($port)"
        fi
    fi
}

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "         VR Recommender - 服务状态"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Neo4j
echo "Neo4j 数据库:"
check_service "Bolt 协议" 7687 ""
check_service "Web UI" 7474 "http://localhost:7474"
echo ""

# Flask API
echo "Flask API 服务:"
check_service "端口 5000" 5000 "http://localhost:5000/health"
check_service "端口 5001" 5001 "http://localhost:5001/health"
echo ""

# 进程信息
echo "运行中的进程:"
ps aux | grep -E "(flask_api|neo4j)" | grep -v grep | while read line; do
    echo "  $line"
done

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
