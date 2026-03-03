#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notify-gateway 主程序
Gateway 监控与通知服务
"""

import sys
import time
import logging
import signal
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigManager
from core.alert_manager import AlertManager
from core.checker import GatewayChecker
from core.notifier import Notifier

# 配置日志
def setup_logging(config):
    """配置日志系统"""
    log_config = config.logging
    
    # 确保日志目录存在
    log_file = Path(log_config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    logging.basicConfig(
        level=getattr(logging, log_config.level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


class NotifyGateway:
    """Gateway 监控与通知服务"""
    
    def __init__(self, config_file=None):
        """
        初始化服务
        
        Args:
            config_file: 配置文件路径
        """
        self.logger = None
        self.running = False
        
        # 加载配置
        self.config = ConfigManager(config_file)
        self.logger = setup_logging(self.config)
        self.logger.info("初始化 notify-gateway 服务...")
        
        # 初始化组件
        self.checker = GatewayChecker(
            host=self.config.gateway.host,
            port=self.config.gateway.port,
            name=self.config.gateway.name
        )
        
        self.alert_mgr = AlertManager(
            min_interval=self.config.alert_control.min_interval,
            max_alerts_per_hour=self.config.alert_control.max_alerts_per_hour,
            quiet_hours=self.config.alert_control.quiet_hours
        )
        
        self.notifier = Notifier(self.config)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("✅ notify-gateway 初始化完成")
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"收到信号 {signum}，准备停止服务...")
        self.running = False
    
    def run(self):
        """运行服务"""
        self.running = True
        self.logger.info("🚀 notify-gateway 服务启动")
        self.logger.info(f"检查间隔：{self.config.gateway.check_interval}秒")
        
        check_interval = self.config.gateway.check_interval
        
        while self.running:
            try:
                # 检查 Gateway 状态
                status = self.checker.check()
                
                if not status.is_ok:
                    self.logger.warning(f"Gateway 异常：{status.error_message}")
                    
                    # 检查是否可以发送告警
                    if self.alert_mgr.can_send_alert():
                        self.logger.info("发送告警通知...")
                        
                        # 获取备份信息
                        backup_info = self.checker.get_backup_info()
                        alert_info = status.to_dict()
                        alert_info['backup_info'] = backup_info
                        
                        # 发送通知
                        results = self.notifier.send_alert(alert_info)
                        
                        # 记录告警
                        self.alert_mgr.record_alert()
                        
                        # 记录结果
                        success_count = sum(1 for r in results.values() if r.get('success'))
                        self.logger.info(f"告警发送完成：{success_count}/{len(results)} 成功")
                        
                        # 自动恢复（如果启用）
                        if self.config.auto_recovery.enabled:
                            self._auto_recovery()
                    else:
                        self.logger.info("告警频率限制，跳过本次通知")
                else:
                    self.logger.debug("Gateway 状态正常")
                    
                    # 如果之前有过告警，现在恢复了，发送恢复通知
                    if self.alert_mgr.last_alert:
                        self.logger.info("Gateway 已恢复，发送恢复通知...")
                        self._send_recovery_notification()
                        self.alert_mgr.record_recovery()
                
                # 等待下次检查
                time.sleep(check_interval)
            
            except KeyboardInterrupt:
                self.logger.info("用户中断")
                break
            except Exception as e:
                self.logger.error(f"运行异常：{e}", exc_info=True)
                time.sleep(60)  # 异常后等待 1 分钟
        
        self.logger.info("notify-gateway 服务已停止")
    
    def _auto_recovery(self):
        """执行自动恢复"""
        if not self.config.auto_recovery.enabled:
            return
        
        self.logger.info("开始自动恢复流程...")
        
        try:
            import subprocess
            
            # 恢复前通知
            if self.config.auto_recovery.notify_before:
                self.logger.info("发送恢复前通知...")
                recovery_info = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'hostname': self.config.gateway.name,
                    'host_ip': self.config.gateway.host,
                    'message': '正在尝试自动恢复 Gateway...',
                }
                self.notifier.send_alert(recovery_info)
            
            # 执行恢复命令
            self.logger.info("执行恢复命令...")
            recover_script = Path.home() / '.openclaw' / 'workspace' / 'backup' / 'recover-gateway.sh'
            
            if recover_script.exists():
                result = subprocess.run(
                    ['bash', str(recover_script)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.logger.info("✅ 自动恢复成功")
                    self._send_recovery_result(True, "自动恢复成功")
                else:
                    self.logger.error(f"❌ 自动恢复失败：{result.stderr}")
                    self._send_recovery_result(False, result.stderr)
            else:
                self.logger.error(f"恢复脚本不存在：{recover_script}")
                self._send_recovery_result(False, "恢复脚本不存在")
        
        except Exception as e:
            self.logger.error(f"自动恢复异常：{e}")
            self._send_recovery_result(False, str(e))
    
    def _send_recovery_notification(self):
        """发送恢复通知"""
        recovery_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'hostname': self.config.gateway.name,
            'host_ip': self.config.gateway.host,
            'process_ok': True,
            'port_ok': True,
            'message': '✅ Gateway 已恢复正常',
        }
        
        # 只发送到 Telegram 和飞书，不发送到小米音箱
        for channel in self.notifier.channels:
            if channel.name in ['telegram', 'feishu', 'ios_bark']:
                channel.send_message(recovery_info, include_recovery=False)
    
    def _send_recovery_result(self, success: bool, message: str):
        """发送恢复结果通知"""
        recovery_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'hostname': self.config.gateway.name,
            'host_ip': self.config.gateway.host,
            'process_ok': success,
            'port_ok': success,
            'message': f"{'✅' if success else '❌'} {message}",
        }
        
        self.notifier.send_alert(recovery_info)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gateway 监控与通知服务')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--test', '-t', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    if args.test:
        # 测试模式
        config = ConfigManager(args.config)
        notifier = Notifier(config)
        
        print("发送测试通知...")
        results = notifier.send_test()
        
        for channel, result in results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {channel}: {result.get('message', result.get('error'))}")
    else:
        # 运行模式
        service = NotifyGateway(args.config)
        service.run()


if __name__ == '__main__':
    main()
