#!/bin/bash
# 检查当前运行的服务和端口

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    当前运行的服务和端口汇总                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Neo4j
echo "🗄️  Neo4j 数据库:"
if nc -z localhost 7687 2>/dev/null; then
    echo "  ✅ Neo4j Bolt (7687): 运行中"
    if curl -s http://localhost:7474 >/dev/null 2>&1; then
        echo "  ✅ Neo4j Web UI (7474): 运行中 - http://localhost:7474"
    fi
else
    echo "  ❌ Neo4j: 未运行"
fi
echo ""

# 检查 Flask API
echo "📊 Flask API 服务:"
if curl -s http://localhost:5000/health >/dev/null 2>&1; then
    echo "  ✅ 端口 5000: 运行中 - http://localhost:5000"
fi
if curl -s http://localhost:5001/health >/dev/null 2>&1; then
    echo "  ✅ 端口 5001: 运行中 - http://localhost:5001"
fi
echo ""

# 检查 HTTP 服务器
echo "🌐 HTTP 服务器:"
if curl -s http://localhost:8001 >/dev/null 2>&1; then
    echo "  ✅ 端口 8001: 运行中 - http://localhost:8001"
fi
echo ""

# 检查其他服务
echo "🔍 其他服务:"
if nc -z localhost 27017 2>/dev/null; then
    echo "  ✅ MongoDB (27017): 运行中"
fi
if curl -s http://localhost:8000 >/dev/null 2>&1; then
    echo "  ✅ ChromaDB (8000): 运行中"
fi
echo ""

# 显示相关进程
echo "📍 进程信息:"
ps aux | grep -E "(flask|python.*server)" | grep -v grep | while read line; do
    echo "  $line"
done
echo ""

echo "═══════════════════════════════════════════════════════════════════"
