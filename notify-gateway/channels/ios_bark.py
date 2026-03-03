#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS Bark 通知渠道
"""

import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BarkChannel:
    """Bark 通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Bark 渠道
        
        Args:
            config: 配置字典
                - enabled: 是否启用
                - bark_url: Bark 推送 URL
                - sound: 通知音
                - level: 通知级别
                - group: 通知分组
                - include_recovery: 是否包含恢复指南
        """
        self.config = config
        self.name = 'ios_bark'
        self.enabled = config.get('enabled', False)
        self.bark_url = config.get('bark_url', '')
        self.sound = config.get('sound', 'alarm')
        self.level = config.get('level', 'timeSensitive')
        self.group = config.get('group', 'OpenClaw')
        self.include_recovery = config.get('include_recovery', True)
    
    def send_message(self, alert_info: Dict[str, Any], include_recovery: Optional[bool] = None) -> Dict[str, Any]:
        """
        发送 iOS 通知
        
        Args:
            alert_info: 告警信息字典
            include_recovery: 是否包含恢复指南（可选，覆盖配置）
        
        Returns:
            dict: 发送结果 {'success': bool, 'message': str}
        """
        if not self.enabled:
            return {'success': False, 'error': 'Bark 渠道未启用'}
        
        if include_recovery is None:
            include_recovery = self.include_recovery
        
        # 构建通知内容
        title = "🚨 Gateway 离线告警"
        body = self._format_message(alert_info, include_recovery)
        
        # Bark API 参数
        params = {
            'title': title,
            'body': body,
            'sound': self.sound,
            'level': self.level,
            'group': self.group,
            'icon': 'https://docs.openclaw.ai/favicon.ico',
            'isArchive': '1' if include_recovery else '0',
        }
        
        # 发送请求
        try:
            logger.info(f"发送 Bark 通知：{title}")
            response = requests.get(self.bark_url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    logger.info("Bark 通知发送成功")
                    return {'success': True, 'message': 'iOS 通知发送成功'}
                else:
                    error_msg = result.get('message', '未知错误')
                    logger.error(f"Bark API 返回错误：{error_msg}")
                    return {'success': False, 'error': f'Bark API 错误：{error_msg}'}
            else:
                logger.error(f"Bark API HTTP 错误：{response.status_code}")
                return {'success': False, 'error': f'HTTP 错误：{response.status_code}'}
        
        except requests.exceptions.Timeout:
            logger.error("Bark 请求超时")
            return {'success': False, 'error': '请求超时'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Bark 请求异常：{e}")
            return {'success': False, 'error': f'网络错误：{str(e)}'}
        except Exception as e:
            logger.error(f"发送 Bark 通知失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def _format_message(self, alert_info: Dict[str, Any], include_recovery: bool) -> str:
        """
        格式化消息内容
        
        Args:
            alert_info: 告警信息
            include_recovery: 是否包含恢复指南
        
        Returns:
            str: 格式化后的消息
        """
        lines = [
            f"时间：{alert_info.get('timestamp', 'N/A')}",
            f"主机：{alert_info.get('hostname', 'N/A')} ({alert_info.get('host_ip', 'N/A')})",
            "",
            "状态检测:",
            f"• Gateway 进程：{'✅ 正常' if alert_info.get('process_ok') else '❌ 不存在'}",
            f"• 18789 端口：{'✅ 监听' if alert_info.get('port_ok') else '❌ 未监听'}",
        ]
        
        # 添加备份信息
        backup_info = alert_info.get('backup_info', {})
        if backup_info:
            lines.extend([
                "",
                "备份状态:",
                f"• 今日备份：{'✅ 已完成' if backup_info.get('today_backup') else '❌ 未完成'}",
                f"• 最新备份：{backup_info.get('latest_backup', 'N/A')}",
                f"• 磁盘使用：{backup_info.get('disk_usage', 'N/A')}",
            ])
        
        if include_recovery:
            lines.extend([
                "",
                "━━━━━━━━━━━━━━",
                "📋 恢复步骤:",
                "",
                "1️⃣ 快速恢复:",
                "bash ~/.openclaw/workspace/backup/recover-gateway.sh",
                "",
                "2️⃣ 手动恢复:",
                "pkill -f openclaw-gateway",
                "cd ~/.openclaw/workspace",
                "nohup node .../openclaw.mjs gateway start > /tmp/openclaw.log 2>&1 &",
                "",
                "3️⃣ 验证:",
                "openclaw status",
                "",
                "详细日志：tail -50 /tmp/openclaw.log",
            ])
        
        return '\n'.join(lines)
    
    def test(self) -> Dict[str, Any]:
        """
        测试通知
        
        Returns:
            dict: 测试结果
        """
        test_info = {
            'timestamp': '测试时间',
            'hostname': '测试主机',
            'host_ip': '127.0.0.1',
            'process_ok': True,
            'port_ok': True,
        }
        return self.send_message(test_info, include_recovery=False)
