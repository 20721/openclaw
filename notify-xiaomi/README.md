# 小米音箱通知服务 (xiaomi-notify)

通过 HTTP API 控制小米/小爱音箱播放 TTS 语音或音频文件的通知服务。

基于 [xiaomusic](https://github.com/hanxi/xiaomusic) 项目实现。

## 功能特性

- 🎯 **独立 HTTP 服务** - 提供 RESTful API，方便其他程序调用
- 🔊 **TTS 文字转语音** - 将任意文字转换为语音播放
- 🎵 **音频 URL 播放** - 支持播放网络音频文件
- 📱 **多设备支持** - 可配置多个音箱设备，通过别名调用
- 🔧 **灵活配置** - 支持自定义端口、音量、超时等参数
- 🚀 **开机自启** - 提供 systemd 服务配置

## 前置要求

1. **已部署 xiaomusic 服务**
   ```bash
   docker run -d --name xiaomusic --restart=always \
     -p 8090:8090 \
     -v /xiaomusic_music:/app/music \
     -v /xiaomusic_conf:/app/conf \
     -e XIAOMUSIC_PUBLIC_PORT=8090 \
     docker.hanxi.cc/hanxi/xiaomusic
   ```

2. **获取小米音箱设备 DID**
   - 访问 xiaomusic 网页后台：`http://你的 IP:8090`
   - 登录小米账号
   - 在设备管理页面查看设备 DID

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/xiaomi-notify.git
cd xiaomi-notify
```

### 2. 配置

```bash
# 复制配置模板
cp config.example.json config.json

# 编辑配置
nano config.json
```

**配置说明：**
```json
{
  "xiaomusic_url": "http://localhost:8090",    // xiaomusic 服务地址
  "default_did": "你的设备 DID",                // 默认设备 DID
  "devices": {                                  // 设备别名映射
    "客厅": "设备 DID 1",
    "卧室": "设备 DID 2"
  },
  "default_volume": 50,                         // 默认音量 (0-100)
  "timeout": 10                                 // HTTP 请求超时 (秒)
}
```

### 3. 启动服务

**手动运行：**
```bash
python3 xiaomi_notify.py --port 9090
```

**后台运行：**
```bash
nohup python3 xiaomi_notify.py --port 9090 > xiaomi_notify.log 2>&1 &
```

**一键安装（systemd 自启）：**
```bash
./install.sh
```

## API 接口

### POST /notify (通用通知接口)

**请求示例：**
```bash
# TTS 文字转语音
curl -X POST http://localhost:9090/notify \
  -H "Content-Type: application/json" \
  -d '{
    "device": "客厅",
    "type": "tts",
    "text": "主人，有重要通知"
  }'

# 播放音频 URL
curl -X POST http://localhost:9090/notify \
  -H "Content-Type: application/json" \
  -d '{
    "device": "客厅",
    "type": "url",
    "url": "http://example.com/alert.mp3"
  }'
```

**参数说明：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device | string | 否 | 设备别名或 DID（不填使用 default_did） |
| type | string | 否 | 通知类型：tts / url（默认 tts） |
| text | string | 否 | TTS 文字（type=tts 时需要） |
| url | string | 否 | 音频 URL（type=url 时需要） |
| volume | number | 否 | 音量 0-100 |

---

### POST /tts (TTS 文字转语音)

```bash
curl -X POST http://localhost:9090/tts \
  -H "Content-Type: application/json" \
  -d '{
    "device": "客厅",
    "text": "你好，这是一条测试通知"
  }'
```

---

### POST /play_url (播放音频 URL)

```bash
curl -X POST http://localhost:9090/play_url \
  -H "Content-Type: application/json" \
  -d '{
    "device": "客厅",
    "url": "http://example.com/audio.mp3"
  }'
```

---

### GET /devices (获取设备列表)

```bash
curl http://localhost:9090/devices
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "configured_devices": {
      "客厅": "123456789",
      "卧室": "987654321"
    },
    "default_did": "123456789",
    "xiaomusic_url": "http://localhost:8090"
  }
}
```

---

### GET /health (健康检查)

```bash
curl http://localhost:9090/health
```

**响应示例：**
```json
{
  "status": "ok",
  "timestamp": "2026-03-03T10:00:00",
  "service": "xiaomi-notify"
}
```

---

## 集成示例

### Shell 脚本

```bash
#!/bin/bash
# 发送通知
send_notify() {
    local message="$1"
    curl -s -X POST http://localhost:9090/notify \
      -H "Content-Type: application/json" \
      -d "{\"device\":\"客厅\",\"text\":\"$message\"}"
}

# 使用
send_notify "Gateway 离线告警！"
```

### Python

```python
import requests

def send_xiaomi_notify(text, device="客厅"):
    """发送小米音箱通知"""
    resp = requests.post("http://localhost:9090/notify", json={
        "device": device,
        "text": text
    })
    return resp.json()

# 使用
result = send_xiaomi_notify("主人，备份完成了！")
print(result)
```

### 集成到现有通知系统

```bash
# 在 notify.sh 中添加
xiaomi_notify() {
    local message="$1"
    local device="${2:-客厅}"
    
    curl -s -X POST http://localhost:9090/notify \
      -H "Content-Type: application/json" \
      -d "{\"device\":\"$device\",\"text\":\"$message\"}"
}

# Gateway 故障通知
gateway_down() {
    xiaomi_notify "🚨 Gateway 离线告警，需要立即处理！" "客厅"
}
```

---

## 文件结构

```
xiaomi-notify/
├── xiaomi_notify.py        # 主程序
├── config.example.json     # 配置模板
├── config.json             # 实际配置（需自行创建，已加入.gitignore）
├── install.sh              # 一键安装脚本
├── xiaomi-notify.service   # systemd 服务配置
├── README.md               # 说明文档
├── LICENSE                 # MIT 许可证
└── .gitignore              # Git 忽略规则
```

---

## 常见问题

### Q: 如何获取设备 DID？

A: 访问 xiaomusic 网页后台 (`http://你的 IP:8090`)，登录后在设备管理页面查看。

### Q: 服务启动失败？

A: 检查：
1. xiaomusic 服务是否正常运行
2. config.json 配置是否正确
3. 端口 9090 是否被占用

### Q: 通知发送成功但音箱没声音？

A: 检查：
1. 音箱是否在线
2. 音箱音量是否合适
3. xiaomusic 日志：`docker logs xiaomusic --tail 50`

---

## 相关项目

- [xiaomusic](https://github.com/hanxi/xiaomusic) - 小爱音箱音乐播放器
- [MiService](https://github.com/yihong0618/MiService) - 小米服务 Python 库

---

## License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 贡献

欢迎提交 Issue 和 Pull Request！
