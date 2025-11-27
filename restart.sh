#!/bin/bash
# 重启所有服务

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

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "         VR Recommender - 重启所有服务"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# 停止所有服务
log_info "停止现有服务..."
./stop_all.sh
sleep 2

# 重新启动 (使用 start_project.sh 的后台模式)
log_info "重新启动所有服务..."
./start_project.sh --background

log_success "重启完成！"
echo ""