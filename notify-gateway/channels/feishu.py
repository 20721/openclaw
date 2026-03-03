#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书通知渠道
"""

import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FeishuChannel:
    """飞书通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化飞书渠道
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.name = 'feishu'
        self.enabled = config.get('enabled', False)
        self.webhook_url = config.get('webhook_url', '')
        self.include_recovery = config.get('include_recovery', True)
    
    def send_message(self, alert_info: Dict[str, Any], include_recovery: Optional[bool] = None) -> Dict[str, Any]:
        """发送飞书消息"""
        if not self.enabled:
            return {'success': False, 'error': '飞书渠道未启用'}
        
        if include_recovery is None:
            include_recovery = self.include_recovery
        
        # 构建消息内容
        content = self._format_message(alert_info, include_recovery)
        
        try:
            logger.info(f"发送飞书通知到 webhook")
            
            # 飞书卡片消息
            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "header": {
                        "template": "red",
                        "title": {
                            "content": "🚨 Gateway 离线告警",
                            "tag": "plain_text"
                        }
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": content
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('StatusCode') == 0 or result.get('code') == 0:
                    logger.info("飞书通知发送成功")
                    return {'success': True, 'message': '飞书通知发送成功'}
                else:
                    error_msg = result.get('msg', result.get('message', '未知错误'))
                    logger.error(f"飞书 API 错误：{error_msg}")
                    return {'success': False, 'error': f'飞书错误：{error_msg}'}
            else:
                logger.error(f"飞书 API HTTP 错误：{response.status_code}")
                return {'success': False, 'error': f'HTTP 错误：{response.status_code}'}
        
        except Exception as e:
            logger.error(f"发送飞书通知失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def _format_message(self, alert_info: Dict[str, Any], include_recovery: bool) -> str:
        """格式化消息内容"""
        lines = [
            f"**时间:** {alert_info.get('timestamp', 'N/A')}",
            f"**主机:** {alert_info.get('hostname', 'N/A')} ({alert_info.get('host_ip', 'N/A')})",
            "",
            "**状态检测:**",
            f"• Gateway 进程：{'✅ 正常' if alert_info.get('process_ok') else '❌ 不存在'}",
            f"• 18789 端口：{'✅ 监听' if alert_info.get('port_ok') else '❌ 未监听'}",
        ]
        
        # 添加备份信息
        backup_info = alert_info.get('backup_info', {})
        if backup_info:
            lines.extend([
                "",
                "**备份状态:**",
                f"• 今日备份：{'✅ 已完成' if backup_info.get('today_backup') else '❌ 未完成'}",
                f"• 最新备份：{backup_info.get('latest_backup', 'N/A')}",
                f"• 磁盘使用：{backup_info.get('disk_usage', 'N/A')}",
            ])
        
        if include_recovery:
            lines.extend([
                "",
                "━━━━━━",
                "**📋 恢复步骤:**",
                "",
                "**1️⃣ 快速恢复:**",
                "```bash",
                "bash ~/.openclaw/workspace/backup/recover-gateway.sh",
                "```",
                "",
                "**2️⃣ 验证:**",
                "```bash",
                "openclaw status",
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
