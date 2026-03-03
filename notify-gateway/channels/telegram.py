#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 通知渠道
"""

import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TelegramChannel:
    """Telegram 通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Telegram 渠道
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.name = 'telegram'
        self.enabled = config.get('enabled', False)
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
        self.include_recovery = config.get('include_recovery', True)
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, alert_info: Dict[str, Any], include_recovery: Optional[bool] = None) -> Dict[str, Any]:
        """发送 Telegram 消息"""
        if not self.enabled:
            return {'success': False, 'error': 'Telegram 渠道未启用'}
        
        if include_recovery is None:
            include_recovery = self.include_recovery
        
        # 构建消息
        text = self._format_message(alert_info, include_recovery)
        
        try:
            logger.info(f"发送 Telegram 通知到 {self.chat_id}")
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True,
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram 通知发送成功")
                return {'success': True, 'message': 'Telegram 通知发送成功'}
            else:
                error = response.json()
                error_msg = error.get('description', '未知错误')
                logger.error(f"Telegram API 错误：{error_msg}")
                return {'success': False, 'error': f'Telegram 错误：{error_msg}'}
        
        except Exception as e:
            logger.error(f"发送 Telegram 通知失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def _format_message(self, alert_info: Dict[str, Any], include_recovery: bool) -> str:
        """格式化消息内容"""
        lines = [
            "🚨 *Gateway 离线告警*",
            "",
            f"时间：`{alert_info.get('timestamp', 'N/A')}`",
            f"主机：`{alert_info.get('hostname', 'N/A')} ({alert_info.get('host_ip', 'N/A')})`",
            "",
            "*状态检测:*",
            f"• Gateway 进程：{'✅ 正常' if alert_info.get('process_ok') else '❌ 不存在'}",
            f"• 18789 端口：{'✅ 监听' if alert_info.get('port_ok') else '❌ 未监听'}",
        ]
        
        # 添加备份信息
        backup_info = alert_info.get('backup_info', {})
        if backup_info:
            lines.extend([
                "",
                "*备份状态:*",
                f"• 今日备份：{'✅ 已完成' if backup_info.get('today_backup') else '❌ 未完成'}",
                f"• 最新备份：`{backup_info.get('latest_backup', 'N/A')}`",
                f"• 磁盘使用：`{backup_info.get('disk_usage', 'N/A')}`",
            ])
        
        if include_recovery:
            lines.extend([
                "",
                "━━━━━━━━━━━━━━━━━━━━",
                "*📋 恢复步骤:*",
                "",
                "*1️⃣ 快速恢复（推荐）:*",
                "```bash",
                "bash ~/.openclaw/workspace/backup/recover-gateway.sh",
                "```",
                "",
                "*2️⃣ 手动恢复:*",
                "```bash",
                "pkill -f openclaw-gateway",
                "sleep 2",
                "cd ~/.openclaw/workspace",
                "nohup node /home/ubuntu/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/openclaw.mjs gateway start > /tmp/openclaw.log 2>&1 &",
                "```",
                "",
                "*3️⃣ 验证:*",
                "```bash",
                "openclaw status",
                "tail -50 /tmp/openclaw.log",
                "```",
            ])
        
        return '\n'.join(lines)
    
    def test(self) -> Dict[str, Any]:
        """测试通知"""
        test_info = {
            'timestamp': '测试时间',
            'hostname': '测试主机',
            'host_ip': '127.0.0.1',
            'process_ok': True,
            'port_ok': True,
        }
        return self.send_message(test_info, include_recovery=False)
