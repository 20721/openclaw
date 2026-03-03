#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - 加载和验证配置文件
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class GatewayConfig:
    name: str = "ubuntu-pc"
    host: str = "192.168.10.30"
    port: int = 18789
    check_interval: int = 300


@dataclass
class AutoRecoveryConfig:
    enabled: bool = False
    max_retries: int = 3
    retry_interval: int = 60
    notify_before: bool = True


@dataclass
class AlertControlConfig:
    min_interval: int = 600
    max_alerts_per_hour: int = 6
    quiet_hours: Dict[str, Any] = field(default_factory=lambda: {"enabled": False})


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "/var/log/notify-gateway/gateway.log"
    max_size: str = "10MB"
    backup_count: int = 5


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认使用 config/config.yaml
        """
        if config_file is None:
            # 默认配置文件路径
            script_dir = Path(__file__).parent.parent
            config_file = script_dir / "config" / "config.yaml"
        
        self.config_file = Path(config_file)
        self.config = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"配置文件不存在：{self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        return self.config
    
    @property
    def gateway(self) -> GatewayConfig:
        """获取 Gateway 配置"""
        cfg = self.config.get('gateway', {})
        return GatewayConfig(
            name=cfg.get('name', 'ubuntu-pc'),
            host=cfg.get('host', '192.168.10.30'),
            port=cfg.get('port', 18789),
            check_interval=cfg.get('check_interval', 300)
        )
    
    @property
    def auto_recovery(self) -> AutoRecoveryConfig:
        """获取自动恢复配置"""
        cfg = self.config.get('auto_recovery', {})
        return AutoRecoveryConfig(
            enabled=cfg.get('enabled', False),
            max_retries=cfg.get('max_retries', 3),
            retry_interval=cfg.get('retry_interval', 60),
            notify_before=cfg.get('notify_before', True)
        )
    
    @property
    def alert_control(self) -> AlertControlConfig:
        """获取告警控制配置"""
        cfg = self.config.get('alert_control', {})
        return AlertControlConfig(
            min_interval=cfg.get('min_interval', 600),
            max_alerts_per_hour=cfg.get('max_alerts_per_hour', 6),
            quiet_hours=cfg.get('quiet_hours', {"enabled": False})
        )
    
    @property
    def logging(self) -> LoggingConfig:
        """获取日志配置"""
        cfg = self.config.get('logging', {})
        return LoggingConfig(
            level=cfg.get('level', 'INFO'),
            file=cfg.get('file', '/var/log/notify-gateway/gateway.log'),
            max_size=cfg.get('max_size', '10MB'),
            backup_count=cfg.get('backup_count', 5)
        )
    
    @property
    def channels(self) -> Dict[str, Dict[str, Any]]:
        """获取所有通知渠道配置"""
        return self.config.get('channels', {})
    
    def get_channel(self, channel_name: str) -> Dict[str, Any]:
        """获取指定渠道配置"""
        channels = self.channels
        return channels.get(channel_name, {})
    
    def is_channel_enabled(self, channel_name: str) -> bool:
        """检查渠道是否启用"""
        channel = self.get_channel(channel_name)
        return channel.get('enabled', False)
    
    def get_enabled_channels(self) -> Dict[str, Dict[str, Any]]:
        """获取所有启用的渠道"""
        enabled = {}
        for name, config in self.channels.items():
            if config.get('enabled', False):
                enabled[name] = config
        return enabled
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        # 检查基础配置
        gateway = self.gateway
        if not gateway.host or not gateway.port:
            raise ValueError("Gateway 配置不完整")
        
        # 检查至少有一个通知渠道
        if not self.get_enabled_channels():
            raise ValueError("至少需要启用一个通知渠道")
        
        # 验证启用的渠道配置
        if self.is_channel_enabled('telegram'):
            tg = self.get_channel('telegram')
            if not tg.get('bot_token') or not tg.get('chat_id'):
                raise ValueError("Telegram 配置不完整")
        
        if self.is_channel_enabled('ios_bark'):
            bark = self.get_channel('ios_bark')
            if not bark.get('bark_url') or bark.get('bark_url') == 'https://api.day.app/YOUR_BARK_KEY':
                raise ValueError("Bark 配置不完整，请替换 YOUR_BARK_KEY")
        
        if self.is_channel_enabled('xiaomi'):
            xiaomi = self.get_channel('xiaomi')
            if not xiaomi.get('device_did'):
                raise ValueError("小米音箱配置不完整")
        
        return True
    
    def __repr__(self) -> str:
        return f"ConfigManager(config_file={self.config_file})"
