#!/bin/bash
# 小米音箱通知服务 - 快速安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="xiaomi-notify"
SERVICE_FILE="$SCRIPT_DIR/xiaomi-notify.service"

echo "=========================================="
echo "🔊 小米音箱通知服务 - 安装脚本"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# 检查配置文件
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo "⚠️  配置文件不存在，正在创建..."
    cp "$SCRIPT_DIR/config.example.json" "$SCRIPT_DIR/config.json"
    echo "📝 请编辑配置文件：nano $SCRIPT_DIR/config.json"
    echo "   填入 xiaomusic 地址和设备 DID"
    echo ""
    read -p "是否现在编辑配置文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano "$SCRIPT_DIR/config.json"
    fi
fi

# 安装 systemd 服务
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  需要 sudo 权限安装 systemd 服务"
    echo "   请输入密码或手动安装"
    SUDO_CMD="sudo"
else
    SUDO_CMD=""
fi

echo ""
echo "📋 安装 systemd 服务..."
$SUDO_CMD cp "$SERVICE_FILE" /etc/systemd/system/
$SUDO_CMD systemctl daemon-reload
$SUDO_CMD systemctl enable $SERVICE_NAME

echo ""
echo "🚀 启动服务..."
$SUDO_CMD systemctl start $SERVICE_NAME

# 检查状态
sleep 2
echo ""
echo "📊 服务状态:"
$SUDO_CMD systemctl status $SERVICE_NAME --no-pager

echo ""
echo "=========================================="
echo "✅ 安装完成!"
echo "=========================================="
echo ""
echo "📍 服务地址：http://localhost:9090"
echo "📋 配置文件：$SCRIPT_DIR/config.json"
echo "📄 日志文件：$SCRIPT_DIR/xiaomi_notify.log"
echo ""
echo "常用命令:"
echo "  查看状态：sudo systemctl status $SERVICE_NAME"
echo "  重启服务：sudo systemctl restart $SERVICE_NAME"
echo "  查看日志：tail -f $SCRIPT_DIR/xiaomi_notify.log"
echo "  停止服务：sudo systemctl stop $SERVICE_NAME"
echo ""
echo "测试通知:"
echo "  python3 $SCRIPT_DIR/xiaomi_notify.py --test"
echo ""
echo "API 调用示例:"
echo '  curl -X POST http://localhost:9090/notify \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '\''{"device":"客厅","text":"测试通知"}'\'''
echo ""
