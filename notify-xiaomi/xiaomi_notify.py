#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小米音箱通知服务 - 独立 HTTP API 服务
通过 xiaomusic 控制小米音箱播放自定义音频/TTS 通知

用法:
    python3 xiaomi_notify.py              # 启动服务 (默认 9090 端口)
    python3 xiaomi_notify.py --port 9091  # 自定义端口
    python3 xiaomi_notify.py --test       # 测试模式 (发送测试通知)

API 接口:
    POST /notify          - 发送通知
    GET  /devices         - 获取设备列表
    GET  /health          - 健康检查
    POST /tts             - TTS 文字转语音
    POST /play_url        - 播放指定 URL 音频

配置:
    cp config.example.json config.json
    编辑 config.json 填入 xiaomusic 服务地址和设备 DID
"""

import json
import argparse
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional, Dict, Any, List

# ============== 配置 ==============
DEFAULT_PORT = 9090
CONFIG_FILE = Path(__file__).parent / "config.json"
LOG_FILE = Path(__file__).parent / "xiaomi_notify.log"

# 默认配置
DEFAULT_CONFIG = {
    "xiaomusic_url": "http://localhost:8090",  # xiaomusic 服务地址
    "default_did": "",  # 默认设备 DID (可选)
    "devices": {
        # 设备别名 -> DID 映射
        # "客厅": "123456789",
        # "卧室": "987654321"
    },
    "default_volume": 50,  # 默认音量 (0-100)
    "timeout": 10  # HTTP 请求超时 (秒)
}

# ============== 日志配置 ==============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 合并默认配置
            return {**DEFAULT_CONFIG, **config}
    else:
        # 创建默认配置文件
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        logger.info(f"配置文件已创建：{CONFIG_FILE}")
        return DEFAULT_CONFIG


def xiaomusic_request(endpoint: str, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    向 xiaomusic 服务发送请求
    
    Args:
        endpoint: API 端点 (如 /cmd)
        data: 请求数据
        config: 配置
    
    Returns:
        响应数据
    """
    url = f"{config['xiaomusic_url']}{endpoint}"
    
    # 构建 JSON 数据
    json_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=config['timeout']) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info(f"xiaomusic 响应：{result}")
            return {"success": True, "data": result}
    except urllib.error.URLError as e:
        logger.error(f"xiaomusic 请求失败：{e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"响应解析失败：{e}")
        return {"success": False, "error": f"响应解析失败：{e}"}


def send_tts(device_did: str, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送 TTS 通知 (文字转语音)
    
    Args:
        device_did: 设备 DID
        text: 要播放的文字
        config: 配置
    
    Returns:
        结果
    """
    logger.info(f"发送 TTS 通知到设备 {device_did}: {text}")
    # 使用 playtts API
    url = f"{config['xiaomusic_url']}/playtts"
    params = f"did={device_did}&text={urllib.parse.quote(text)}"
    
    req = urllib.request.Request(
        f"{url}?{params}",
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=config['timeout']) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info(f"xiaomusic 响应：{result}")
            return {"success": True, "data": result}
    except urllib.error.URLError as e:
        logger.error(f"xiaomusic 请求失败：{e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"响应解析失败：{e}")
        return {"success": False, "error": f"响应解析失败：{e}"}


def play_audio_url(device_did: str, audio_url: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    播放指定 URL 的音频
    
    Args:
        device_did: 设备 DID
        audio_url: 音频文件 URL
        config: 配置
    
    Returns:
        结果
    """
    logger.info(f"播放音频 URL 到设备 {device_did}: {audio_url}")
    return xiaomusic_request("/cmd", {
        "did": device_did,
        "cmd": f"播放 {audio_url}"
    }, config)


def get_devices(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取设备列表 (从配置中读取)
    
    Returns:
        设备列表
    """
    devices = config.get('devices', {})
    return {
        "success": True,
        "data": {
            "configured_devices": devices,
            "default_did": config.get('default_did', ''),
            "xiaomusic_url": config.get('xiaomusic_url', '')
        }
    }


# ============== HTTP 服务 ==============
class NotifyHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    config = None  # 类变量，在启动时设置
    
    def log_message(self, format, *args):
        """重定向日志到 logger"""
        logger.info(f"HTTP: {args[0]}")
    
    def send_json_response(self, data: Dict[str, Any], status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/health':
            # 健康检查
            self.send_json_response({
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "service": "xiaomi-notify"
            })
        
        elif path == '/devices':
            # 获取设备列表
            result = get_devices(self.config)
            self.send_json_response(result)
        
        elif path == '/config':
            # 获取当前配置 (隐藏敏感信息)
            safe_config = {
                "xiaomusic_url": self.config.get('xiaomusic_url'),
                "default_did": self.config.get('default_did'),
                "devices": list(self.config.get('devices', {}).keys()),
                "default_volume": self.config.get('default_volume'),
                "timeout": self.config.get('timeout')
            }
            self.send_json_response({"success": True, "data": safe_config})
        
        else:
            self.send_json_response({
                "success": False,
                "error": "未知端点",
                "available_endpoints": [
                    "GET /health - 健康检查",
                    "GET /devices - 获取设备列表",
                    "GET /config - 获取配置",
                    "POST /notify - 发送通知",
                    "POST /tts - TTS 文字转语音",
                    "POST /play_url - 播放 URL 音频"
                ]
            }, 404)
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
        
        # 解析 JSON 或表单数据
        try:
            if self.headers.get('Content-Type', '').startswith('application/json'):
                params = json.loads(body) if body else {}
            else:
                params = dict(parse_qs(body))
                # 解析表单数组值
                params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        except json.JSONDecodeError as e:
            self.send_json_response({"success": False, "error": f"JSON 解析失败：{e}"}, 400)
            return
        
        if path == '/notify':
            # 发送通知 (通用接口)
            self.handle_notify(params)
        
        elif path == '/tts':
            # TTS 文字转语音
            self.handle_tts(params)
        
        elif path == '/play_url':
            # 播放 URL 音频
            self.handle_play_url(params)
        
        else:
            self.send_json_response({"success": False, "error": "未知端点"}, 404)
    
    def handle_notify(self, params: Dict[str, Any]):
        """
        处理 /notify 请求
        
        参数:
            - device: 设备别名或 DID (可选，使用默认设备)
            - type: 通知类型 "tts" 或 "url" (可选，默认 tts)
            - text: TTS 文字 (type=tts 时需要)
            - url: 音频 URL (type=url 时需要)
            - volume: 音量 0-100 (可选)
        """
        device = params.get('device', self.config.get('default_did', ''))
        notify_type = params.get('type', 'tts')
        volume = params.get('volume', self.config.get('default_volume'))
        
        # 解析设备别名
        if device in self.config.get('devices', {}):
            device = self.config['devices'][device]
        
        if not device:
            self.send_json_response({
                "success": False,
                "error": "未指定设备 DID，请在配置中设置 default_did 或请求时指定 device 参数"
            }, 400)
            return
        
        if notify_type == 'tts':
            text = params.get('text', '')
            if not text:
                self.send_json_response({"success": False, "error": "缺少 text 参数"}, 400)
                return
            result = send_tts(device, text, self.config)
        
        elif notify_type == 'url':
            url = params.get('url', '')
            if not url:
                self.send_json_response({"success": False, "error": "缺少 url 参数"}, 400)
                return
            result = play_audio_url(device, url, self.config)
        
        else:
            self.send_json_response({
                "success": False,
                "error": f"不支持的通知类型：{notify_type}",
                "supported_types": ["tts", "url"]
            }, 400)
            return
        
        self.send_json_response(result)
    
    def handle_tts(self, params: Dict[str, Any]):
        """
        处理 /tts 请求
        
        参数:
            - device: 设备别名或 DID
            - text: 要播放的文字
            - volume: 音量 (可选)
        """
        device = params.get('device', self.config.get('default_did', ''))
        text = params.get('text', '')
        
        if not device:
            self.send_json_response({"success": False, "error": "缺少 device 参数"}, 400)
            return
        
        if not text:
            self.send_json_response({"success": False, "error": "缺少 text 参数"}, 400)
            return
        
        # 解析设备别名
        if device in self.config.get('devices', {}):
            device = self.config['devices'][device]
        
        result = send_tts(device, text, self.config)
        self.send_json_response(result)
    
    def handle_play_url(self, params: Dict[str, Any]):
        """
        处理 /play_url 请求
        
        参数:
            - device: 设备别名或 DID
            - url: 音频文件 URL
            - volume: 音量 (可选)
        """
        device = params.get('device', self.config.get('default_did', ''))
        url = params.get('url', '')
        
        if not device:
            self.send_json_response({"success": False, "error": "缺少 device 参数"}, 400)
            return
        
        if not url:
            self.send_json_response({"success": False, "error": "缺少 url 参数"}, 400)
            return
        
        # 解析设备别名
        if device in self.config.get('devices', {}):
            device = self.config['devices'][device]
        
        result = play_audio_url(device, url, self.config)
        self.send_json_response(result)


def test_notify(config: Dict[str, Any]):
    """测试模式 - 发送测试通知"""
    device = config.get('default_did', '')
    if not device:
        logger.error("未配置 default_did，无法发送测试通知")
        return
    
    logger.info("发送测试通知...")
    result = send_tts(device, "测试通知，小爱音箱服务正常运行", config)
    
    if result.get('success'):
        logger.info("✅ 测试通知发送成功")
    else:
        logger.error(f"❌ 测试通知发送失败：{result.get('error')}")


def main():
    parser = argparse.ArgumentParser(description='小米音箱通知服务')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'服务端口 (默认：{DEFAULT_PORT})')
    parser.add_argument('--test', action='store_true', help='测试模式：发送测试通知后退出')
    parser.add_argument('--init-config', action='store_true', help='初始化配置文件后退出')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 初始化配置模式
    if args.init_config:
        logger.info(f"配置文件已就绪：{CONFIG_FILE}")
        return
    
    # 测试模式
    if args.test:
        test_notify(config)
        return
    
    # 启动 HTTP 服务
    NotifyHandler.config = config
    server = HTTPServer(('0.0.0.0', args.port), NotifyHandler)
    
    logger.info("=" * 50)
    logger.info("🔊 小米音箱通知服务已启动")
    logger.info(f"📍 监听端口：{args.port}")
    logger.info(f"🔗 xiaomusic 服务：{config['xiaomusic_url']}")
    logger.info(f"📋 默认设备：{config.get('default_did', '未配置')}")
    logger.info("=" * 50)
    logger.info("API 接口:")
    logger.info("  POST /notify    - 发送通知 (通用)")
    logger.info("  POST /tts       - TTS 文字转语音")
    logger.info("  POST /play_url  - 播放 URL 音频")
    logger.info("  GET  /devices   - 获取设备列表")
    logger.info("  GET  /health    - 健康检查")
    logger.info("=" * 50)
    logger.info(f"日志文件：{LOG_FILE}")
    logger.info(f"配置文件：{CONFIG_FILE}")
    logger.info("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n正在关闭服务...")
        server.shutdown()
        logger.info("服务已关闭")


if __name__ == '__main__':
    main()
