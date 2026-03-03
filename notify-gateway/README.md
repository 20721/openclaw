# notify-gateway

> Gateway 监控与多渠道通知服务

## 功能特性

- 🔍 **Gateway 状态监控** - 进程、端口、健康检查
- 📢 **多渠道通知** - Telegram、飞书、小米音箱、iOS Bark
- 🔊 **语音告警** - 小米音箱语音播报
- 📱 **手机推送** - iOS Bark 推送通知
- ⚙️ **自动恢复** - 可选的自动恢复功能
- 🎛️ **频率控制** - 告警间隔、免打扰时段
- 📝 **恢复指南** - 详细的故障恢复步骤

## 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/tools/notify-gateway
pip3 install -r requirements.txt
```

### 2. 配置

编辑 `config/config.yaml`：

```yaml
gateway:
  name: "ubuntu-pc"
  host: "192.168.10.30"
  port: 18789

channels:
  # Telegram
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
  
  # iOS Bark
  ios_bark:
    enabled: true
    bark_url: "https://api.day.app/YOUR_BARK_KEY"
  
  # 小米音箱
  xiaomi:
    enabled: true
    device_did: "981599844"
    alert_volume: 80
    restore_volume: 50
```

### 3. 测试

```bash
python3 main.py --test
```

### 4. 运行

```bash
# 前台运行
python3 main.py

# 后台运行
nohup python3 main.py > notify-gateway.log 2>&1 &
```

## 配置说明

### 基础配置

```yaml
gateway:
  name: "ubuntu-pc"           # 主机名称
  host: "192.168.10.30"       # 主机 IP
  port: 18789                 # Gateway 端口
  check_interval: 300         # 检查间隔（秒）
```

### 自动恢复

```yaml
auto_recovery:
  enabled: false              # 是否启用自动恢复
  max_retries: 3              # 最大重试次数
  retry_interval: 60          # 重试间隔（秒）
  notify_before: true         # 恢复前是否通知
```

### 告警频率控制

```yaml
alert_control:
  min_interval: 600           # 最小告警间隔（秒）
  max_alerts_per_hour: 6      # 每小时最大告警次数
  quiet_hours:
    enabled: false            # 免打扰时段
    start: "23:00"
    end: "07:00"
```

### 通知渠道

#### Telegram

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
  include_recovery: true      # 包含恢复指南
```

#### 飞书

```yaml
feishu:
  enabled: false
  webhook_url: "YOUR_WEBHOOK_URL"
  include_recovery: true
```

#### 小米音箱

```yaml
xiaomi:
  enabled: true
  xiaomusic_url: "http://192.168.10.30:8090"
  device_did: "981599844"     # 设备 DID
  alert_volume: 80            # 告警音量
  restore_volume: 50          # 恢复音量
  alert_message: "主人，Gateway 离线了"
```

#### iOS Bark

```yaml
ios_bark:
  enabled: true
  bark_url: "https://api.day.app/YOUR_BARK_KEY"
  sound: "alarm"              # 通知音
  level: "timeSensitive"      # 通知级别
  group: "OpenClaw"           # 通知分组
  include_recovery: true
```

## 使用示例

### 测试通知

```bash
python3 main.py --test
```

### 查看状态

```bash
# 查看服务状态
systemctl status notify-gateway

# 查看日志
tail -f /var/log/notify-gateway/gateway.log
```

## 项目结构

```
notify-gateway/
├── main.py                   # 主程序
├── core/
│   ├── config_manager.py     # 配置管理
│   ├── alert_manager.py      # 告警频率控制
│   ├── checker.py            # Gateway 检查
│   └── notifier.py           # 通知管理
├── channels/
│   ├── telegram.py           # Telegram 渠道
│   ├── feishu.py             # 飞书渠道
│   ├── xiaomi.py             # 小米音箱渠道
│   └── ios_bark.py           # iOS Bark 渠道
├── config/
│   └── config.yaml           # 配置文件
├── requirements.txt          # Python 依赖
└── README.md                 # 本文档
```

## 通知渠道对比

| 渠道 | 恢复指南 | 适用场景 | 配置难度 |
|------|----------|----------|----------|
| Telegram | ✅ | 详细消息、可交互 | ⭐⭐ |
| 飞书 | ✅ | 企业用户、团队协作 | ⭐⭐ |
| 小米音箱 | ❌ | 语音告警、在家场景 | ⭐ |
| iOS Bark | ✅ | 手机推送、随身携带 | ⭐ |

## 常见问题

### Q: Bark 如何获取推送 URL？

A: 在 iPhone 上安装 Bark App，打开后会显示推送 URL，复制到配置文件即可。

### Q: 如何设置免打扰时段？

A: 在 `alert_control.quiet_hours` 中配置 `start` 和 `end` 时间。

### Q: 自动恢复安全吗？

A: 默认不启用。启用后会在恢复前发送通知，你可以随时关闭。

## License

MIT License
