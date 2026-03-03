#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway 状态检查器
"""

import socket
import subprocess
import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GatewayStatus:
    """Gateway 状态数据类"""
    is_ok: bool = False
    process_ok: bool = False
    port_ok: bool = False
    health_ok: bool = False
    pid: Optional[int] = None
    hostname: str = ""
    host_ip: str = ""
    timestamp: str = ""
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_ok': self.is_ok,
            'process_ok': self.process_ok,
            'port_ok': self.port_ok,
            'health_ok': self.health_ok,
            'pid': self.pid,
            'hostname': self.hostname,
            'host_ip': self.host_ip,
            'timestamp': self.timestamp,
            'error_message': self.error_message,
        }


class GatewayChecker:
    """Gateway 状态检查器"""
    
    def __init__(self, host: str = "192.168.10.30", port: int = 18789, name: str = "ubuntu-pc"):
        """
        初始化检查器
        
        Args:
            host: Gateway 主机 IP
            port: Gateway 端口
            name: 主机名称
        """
        self.host = host
        self.port = port
        self.name = name
    
    def check(self) -> GatewayStatus:
        """
        检查 Gateway 状态
        
        Returns:
            GatewayStatus: 状态对象
        """
        status = GatewayStatus(
            hostname=self.name,
            host_ip=self.host,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 检查进程
        status.process_ok = self._check_process()
        
        # 检查端口
        status.port_ok = self._check_port()
        
        # 检查健康 API
        status.health_ok = self._check_health_api()
        
        # 获取 PID
        if status.process_ok:
            status.pid = self._get_pid()
        
        # 综合判断
        status.is_ok = status.process_ok and status.port_ok
        
        if not status.is_ok:
            if not status.process_ok:
                status.error_message = "Gateway 进程不存在"
            elif not status.port_ok:
                status.error_message = f"端口 {self.port} 未监听"
        
        logger.info(f"Gateway 状态检查完成：{'正常' if status.is_ok else '异常'} - {status.error_message}")
        return status
    
    def _check_process(self) -> bool:
        """检查 Gateway 进程是否存在"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'openclaw-gateway'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"检查进程失败：{e}")
            return False
    
    def _check_port(self) -> bool:
        """检查端口是否监听"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"检查端口失败：{e}")
            return False
    
    def _check_health_api(self) -> bool:
        """检查健康 API"""
        try:
            url = f"http://{self.host}:{self.port}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"健康 API 检查失败：{e}")
            return False
    
    def _get_pid(self) -> Optional[int]:
        """获取 Gateway 进程 PID"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'openclaw-gateway'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return int(pids[0]) if pids else None
        except Exception as e:
            logger.error(f"获取 PID 失败：{e}")
        return None
    
    def get_backup_info(self) -> Dict[str, Any]:
        """获取备份信息"""
        import os
        from pathlib import Path
        
        backup_dir = Path.home() / '.openclaw' / 'workspace' / 'backup' / 'monitor' / 'backups'
        backup_log = Path.home() / '.openclaw' / 'workspace' / 'backup' / 'disaster_recovery' / 'backup_log.txt'
        
        info = {
            'backup_ok': False,
            'latest_backup': None,
            'today_backup': False,
            'disk_usage': self._get_disk_usage(),
        }
        
        try:
            # 检查今日备份
            if backup_log.exists():
                with open(backup_log, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        today = datetime.now().strftime('%Y-%m-%d')
                        if today in last_line and '成功' in last_line:
                            info['today_backup'] = True
                            info['backup_ok'] = True
            
            # 获取最新备份文件
            if backup_dir.exists():
                backup_files = list(backup_dir.glob('*.json'))
                if backup_files:
                    latest = max(backup_files, key=lambda f: f.stat().st_mtime)
                    info['latest_backup'] = latest.name
        except Exception as e:
            logger.error(f"获取备份信息失败：{e}")
        
        return info
    
    def _get_disk_usage(self) -> str:
        """获取磁盘使用情况"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            percent = (used / total) * 100
            return f"{used // (1024**3)}GB/{total // (1024**3)}GB ({percent:.0f}%)"
        except Exception as e:
            logger.error(f"获取磁盘信息失败：{e}")
            return "未知"
