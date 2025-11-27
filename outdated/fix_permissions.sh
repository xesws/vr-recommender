#!/bin/bash
# 修复脚本权限问题

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              权限修复工具 - 解决 HTTP 403 错误                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 修复权限函数
fix_script_permissions() {
    local script=$1
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo -e "${GREEN}✓${NC} 已修复: $script"
    else
        echo -e "${RED}✗${NC} 未找到: $script"
    fi
}

echo "🔧 正在修复所有脚本权限..."
echo ""

# 修复关键脚本
fix_script_permissions "start_project.sh"
fix_script_permissions "start_services.sh"
fix_script_permissions "stop_all.sh"
fix_script_permissions "restart.sh"
fix_script_permissions "status.sh"
fix_script_permissions "diagnose.sh"
fix_script_permissions "check_ports.sh"

echo ""
echo "═══════════════════════════════════════════════════════════════════"

# 检查 Python 环境
echo ""
echo "🐍 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python3 已安装: $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python3 未安装"
fi

# 检查 Neo4j
echo ""
echo "🗄️  检查 Neo4j..."
if command -v neo4j &> /dev/null; then
    echo -e "${GREEN}✓${NC} Neo4j 已安装"
    if nc -z localhost 7687 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Neo4j 正在运行"
    else
        echo -e "${YELLOW}!${NC} Neo4j 未运行，尝试启动..."
        neo4j start 2>/dev/null || echo -e "${RED}✗${NC} 启动失败，请手动运行: neo4j start"
    fi
else
    echo -e "${RED}✗${NC} Neo4j 未安装"
fi

# 检查端口
echo ""
echo "🔌 检查端口占用..."
for port in 5000 5001 7474 7687; do
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓${NC} 端口 $port: 被占用"
    else
        echo -e "${YELLOW}!${NC} 端口 $port: 空闲"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✅ 权限修复完成！${NC}"
echo ""
echo "📋 下一步:"
echo "   1. 在终端中运行: ./start_project.sh"
echo "   2. 访问网页: http://127.0.0.1/index.html"
echo "   3. 或直接访问: http://127.0.0.1:5001"
echo ""
echo "💡 记住:"
echo "   • .sh 脚本必须在终端运行，不是在浏览器中打开"
echo "   • 如果仍有问题，运行: ./diagnose.sh"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
