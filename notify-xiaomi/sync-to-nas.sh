#!/bin/bash
# 同步项目到群晖 NAS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="xiaomi-notify"
NAS_HOST="192.168.10.6"
NAS_USER="openclaw"
NAS_PASS="TqleHG"
REMOTE_DIR="/openclaw/projects/${PROJECT_NAME}"

echo "=========================================="
echo "📦 同步 ${PROJECT_NAME} 到群晖 NAS"
echo "=========================================="

# 创建远程目录
echo "📁 创建远程目录..."
lftp -u "${NAS_USER},${NAS_PASS}" "${NAS_HOST}" << EOF
mkdir -p ${REMOTE_DIR}
bye
EOF

# 上传文件（排除敏感文件）
echo "📤 上传文件..."
cd "${SCRIPT_DIR}"

# 创建要上传的文件列表
FILES_TO_UPLOAD=(
    "xiaomi_notify.py"
    "config.example.json"
    "README.md"
    "LICENSE"
    "DEPLOY.md"
    "PROJECT_SUMMARY.md"
    "install.sh"
    "xiaomi-notify.service"
    ".gitignore"
)

# 逐个上传
for file in "${FILES_TO_UPLOAD[@]}"; do
    if [ -f "$file" ]; then
        echo "  → ${file}"
        lftp -u "${NAS_USER},${NAS_PASS}" "${NAS_HOST}" << EOF
cd ${REMOTE_DIR}
put ${file}
bye
EOF
    fi
done

echo ""
echo "=========================================="
echo "✅ 同步完成!"
echo "=========================================="
echo ""
echo "远程路径：${REMOTE_DIR}"
echo "访问地址：smb://${NAS_HOST}/openclaw/projects/${PROJECT_NAME}/"
echo ""
