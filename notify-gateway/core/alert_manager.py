#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理器 - 控制告警频率
"""

from datetime import datetime, timedelta
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AlertManager:
    """告警管理器"""
    
    def __init__(self, min_interval: int = 600, max_alerts_per_hour: int = 6,
                 quiet_hours: Optional[dict] = None):
        """
        初始化告警管理器
        
        Args:
            min_interval: 最小告警间隔（秒），默认 600 秒（10 分钟）
            max_alerts_per_hour: 每小时最大告警次数，默认 6 次
            quiet_hours: 免打扰时段配置 {"enabled": False, "start": "23:00", "end": "07:00"}
        """
        self.min_interval = min_interval
        self.max_alerts_per_hour = max_alerts_per_hour
        self.quiet_hours = quiet_hours or {"enabled": False}
        
        self.alert_history = deque()  # 告警历史队列
        self.last_alert: Optional[datetime] = None
        self.last_recovery: Optional[datetime] = None
    
    def can_send_alert(self) -> bool:
        """
        检查是否可以发送告警
        
        Returns:
            bool: True 表示可以发送，False 表示需要抑制
        """
        now = datetime.now()
        
        # 检查免打扰时段
        if self._is_quiet_hours(now):
            logger.info("当前在免打扰时段，抑制告警")
            return False
        
        # 检查最小间隔
        if self.last_alert:
            time_since_last = (now - self.last_alert).total_seconds()
            if time_since_last < self.min_interval:
                logger.info(f"距离上次告警仅 {time_since_last:.0f} 秒，小于最小间隔 {self.min_interval} 秒")
                return False
        
        # 检查每小时最大次数
        hour_ago = now - timedelta(hours=1)
        recent_alerts = [a for a in self.alert_history if a > hour_ago]
        
        if len(recent_alerts) >= self.max_alerts_per_hour:
            logger.warning(f"过去 1 小时内已发送 {len(recent_alerts)} 次告警，达到上限 {self.max_alerts_per_hour}")
            return False
        
        logger.info("告警频率检查通过，可以发送")
        return True
    
    def record_alert(self):
        """记录一次告警"""
        now = datetime.now()
        self.last_alert = now
        self.alert_history.append(now)
        
        # 清理旧记录（保留最近 1 小时）
        hour_ago = now - timedelta(hours=1)
        while self.alert_history and self.alert_history[0] < hour_ago:
            self.alert_history.popleft()
        
        logger.info(f"已记录告警，当前小时告警次数：{len(self.alert_history)}")
    
    def record_recovery(self):
        """记录一次恢复"""
        self.last_recovery = datetime.now()
        logger.info("已记录恢复事件")
    
    def _is_quiet_hours(self, now: datetime) -> bool:
        """
        检查当前是否在免打扰时段
        
        Args:
            now: 当前时间
        
        Returns:
            bool: True 表示在免打扰时段
        """
        if not self.quiet_hours.get('enabled', False):
            return False
        
        try:
            start_str = self.quiet_hours.get('start', '23:00')
            end_str = self.quiet_hours.get('end', '07:00')
            
            start_hour, start_minute = map(int, start_str.split(':'))
            end_hour, end_minute = map(int, end_str.split(':'))
            
            current_time = now.hour * 60 + now.minute
            start_time = start_hour * 60 + start_minute
            end_time = end_hour * 60 + end_minute
            
            # 处理跨天情况（如 23:00 - 07:00）
            if start_time > end_time:
                # 跨天：23:00 - 07:00
                return current_time >= start_time or current_time < end_time
            else:
                # 不跨天：如 01:00 - 03:00
                return start_time <= current_time < end_time
        
        except Exception as e:
            logger.error(f"检查免打扰时段出错：{e}")
            return False
    
    def get_status(self) -> dict:
        """
        获取告警管理器状态
        
        Returns:
            dict: 状态信息
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        recent_alerts = len([a for a in self.alert_history if a > hour_ago])
        
        return {
            'last_alert': self.last_alert.isoformat() if self.last_alert else None,
            'last_recovery': self.last_recovery.isoformat() if self.last_recovery else None,
            'alerts_last_hour': recent_alerts,
            'max_alerts_per_hour': self.max_alerts_per_hour,
            'min_interval_seconds': self.min_interval,
            'quiet_hours_enabled': self.quiet_hours.get('enabled', False),
            'in_quiet_hours': self._is_quiet_hours(now),
        }
    
    def reset(self):
        """重置告警管理器"""
        self.alert_history.clear()
        self.last_alert = None
        self.last_recovery = None
        logger.info("告警管理器已重置")
