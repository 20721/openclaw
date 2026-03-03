#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小米音箱通知渠道
"""

import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class XiaomiChannel:
    """小米音箱通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化小米音箱渠道
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.name = 'xiaomi'
        self.enabled = config.get('enabled', False)
        self.xiaomusic_url = config.get('xiaomusic_url', 'http://localhost:8090')
        self.device_did = config.get('device_did', '')
        self.alert_volume = config.get('alert_volume', 80)
        self.restore_volume = config.get('restore_volume', 50)
        self.alert_message = config.get('alert_message', '主人，Gateway 离线了')
        self.original_volume: Optional[int] = None
    
    def send_voice_alert(self, alert_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送语音告警（不含恢复指南）
        
        Args:
            alert_info: 告警信息（本渠道不使用）
        
        Returns:
            dict: 发送结果
        """
        if not self.enabled:
            return {'success': False, 'error': '小米音箱渠道未启用'}
        
        try:
            logger.info(f"发送小米音箱语音告警：{self.alert_message}")
            
            # 1. 获取当前音量（用于恢复）
            self._get_current_volume()
            
            # 2. 设置告警音量
            self._set_volume(self.alert_volume)
            
            # 3. 播放语音
            result = self._play_tts(self.alert_message)
            
            # 4. 恢复音量
            self._restore_volume()
            
            return result
        
        except Exception as e:
            logger.error(f"发送小米音箱告警失败：{e}")
            return {'success': False, 'error': str(e)}
    
    def _get_current_volume(self) -> int:
        """获取当前音量"""
        try:
            url = f"{self.xiaomusic_url}/getvolume"
            params = {'did': self.device_did}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.original_volume = data.get('volume', 50)
                logger.debug(f"当前音量：{self.original_volume}")
                return self.original_volume
        except Exception as e:
            logger.warning(f"获取音量失败：{e}，使用默认值")
            self.original_volume = 50
        return 50
    
    def _set_volume(self, volume: int) -> bool:
        """设置音量"""
        try:
            url = f"{self.xiaomusic_url}/setvolume"
            data = {'did': self.device_did, 'volume': volume}
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code == 200:
                logger.debug(f"音量已设置为：{volume}")
                return True
        except Exception as e:
            logger.error(f"设置音量失败：{e}")
        return False
    
    def _play_tts(self, text: str) -> Dict[str, Any]:
        """播放 TTS"""
        try:
            url = f"{self.xiaomusic_url}/playtts"
            params = {'did': self.device_did, 'text': text}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info("TTS 播放成功")
                return {'success': True, 'message': '小米音箱语音播放成功'}
            else:
                logger.error(f"TTS 播放失败：HTTP {response.status_code}")
                return {'success': False, 'error': f'HTTP 错误：{response.status_code}'}
        
        except Exception as e:
            logger.error(f"TTS 播放异常：{e}")
            return {'success': False, 'error': str(e)}
    
    def _restore_volume(self):
        """恢复音量"""
        if self.original_volume is not None:
            logger.debug(f"恢复音量到：{self.original_volume}")
            self._set_volume(self.original_volume)
        else:
            logger.debug(f"恢复音量到：{self.restore_volume}")
            self._set_volume(self.restore_volume)
    
    def test(self) -> Dict[str, Any]:
        """测试通知"""
        return self.send_voice_alert({})
