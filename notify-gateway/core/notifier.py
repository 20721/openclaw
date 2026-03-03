#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知管理器 - 统一管理所有通知渠道
"""

import logging
from typing import Dict, Any, List
from .config_manager import ConfigManager

# 导入所有渠道
from ..channels.telegram import TelegramChannel
from ..channels.feishu import FeishuChannel
from ..channels.xiaomi import XiaomiChannel
from ..channels.ios_bark import BarkChannel

logger = logging.getLogger(__name__)


class Notifier:
    """通知管理器"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化通知管理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.channels: List[Any] = []
        self._init_channels()
    
    def _init_channels(self):
        """初始化所有启用的渠道"""
        channel_configs = self.config.channels
        
        # Telegram
        if self.config.is_channel_enabled('telegram'):
            self.channels.append(TelegramChannel(channel_configs['telegram']))
            logger.info("✅ Telegram 渠道已初始化")
        
        # 飞书
        if self.config.is_channel_enabled('feishu'):
            self.channels.append(FeishuChannel(channel_configs['feishu']))
            logger.info("✅ 飞书渠道已初始化")
        
        # 小米音箱
        if self.config.is_channel_enabled('xiaomi'):
            self.channels.append(XiaomiChannel(channel_configs['xiaomi']))
            logger.info("✅ 小米音箱渠道已初始化")
        
        # iOS Bark
        if self.config.is_channel_enabled('ios_bark'):
            self.channels.append(BarkChannel(channel_configs['ios_bark']))
            logger.info("✅ iOS Bark 渠道已初始化")
        
        logger.info(f"已初始化 {len(self.channels)} 个通知渠道")
    
    def send_alert(self, alert_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        发送告警通知到所有渠道
        
        Args:
            alert_info: 告警信息字典
        
        Returns:
            dict: 各渠道发送结果
        """
        results = {}
        
        logger.info(f"开始发送告警通知到 {len(self.channels)} 个渠道")
        
        for channel in self.channels:
            try:
                # 小米音箱不发送恢复指南
                if channel.name == 'xiaomi':
                    result = channel.send_voice_alert(alert_info)
                else:
                    # 其他渠道根据配置决定是否包含恢复指南
                    include_recovery = getattr(channel, 'include_recovery', True)
                    result = channel.send_message(alert_info, include_recovery=include_recovery)
                
                results[channel.name] = result
                logger.info(f"{channel.name} 渠道发送结果：{'成功' if result.get('success') else '失败'}")
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"{channel.name} 渠道发送异常：{error_msg}")
                results[channel.name] = {'success': False, 'error': error_msg}
        
        return results
    
    def send_test(self) -> Dict[str, Dict[str, Any]]:
        """
        发送测试通知到所有渠道
        
        Returns:
            dict: 各渠道测试结果
        """
        results = {}
        
        logger.info("开始发送测试通知")
        
        for channel in self.channels:
            try:
                if hasattr(channel, 'test'):
                    result = channel.test()
                    results[channel.name] = result
                else:
                    results[channel.name] = {'success': False, 'error': '不支持测试'}
            except Exception as e:
                results[channel.name] = {'success': False, 'error': str(e)}
        
        return results
    
    def get_channel_status(self) -> Dict[str, bool]:
        """
        获取所有渠道状态
        
        Returns:
            dict: 渠道名称 -> 是否启用
        """
        return {
            channel.name: channel.enabled
            for channel in self.channels
        }
