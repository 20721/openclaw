# 小米音箱通知服务 - 项目开发总结

**项目时间**: 2026-03-03  
**开发环境**: Ubuntu 24.04, Python 3.12, Docker  
**项目名称**: xiaomi-notify

---

## 📋 项目背景

### 需求来源

主人希望实现一个功能：**通过程序控制小米智能音箱播放自定义通知**，比如：
- Gateway 离线告警
- 备份完成通知
- 系统重要事件提醒

### 目标

1. 独立的 HTTP API 服务，方便其他程序调用
2. 支持 TTS 文字转语音
3. 支持播放网络音频 URL
4. 配置简单，隐私信息安全

---

## 🛠️ 技术选型

### 核心依赖

| 组件 | 版本 | 用途 |
|------|------|------|
| xiaomusic | 0.4.23 | 小米音箱控制服务 |
| Python | 3.12 | 通知服务开发语言 |
| Docker | 24.0 | xiaomusic 容器化部署 |
| HTTP Server | Python 内置 | API 服务 |

### 为什么选择 xiaomusic？

1. **成熟稳定** - GitHub 5.4k+ stars，活跃维护中
2. **功能完整** - 支持 TTS、音乐播放、设备管理
3. **部署简单** - Docker 一键部署
4. **API 开放** - 提供 RESTful API

---

## 🚧 开发过程

### 阶段 1: xiaomusic 部署

**命令**:
```bash
docker run -d --name xiaomusic --restart=always \
  -p 8090:8090 \
  -v /xiaomusic_music:/app/music \
  -v /xiaomusic_conf:/app/conf \
  -e XIAOMUSIC_PUBLIC_PORT=8090 \
  docker.hanxi.cc/hanxi/xiaomusic
```

**状态**: ✅ 成功

---

### 阶段 2: 获取设备 DID

#### 遇到的问题 1: 账号密码登录失败

**现象**:
```
Exception: Error https://api2.mina.mi.com/admin/v2/device_list?master=0: Login failed
KeyError: 'userId'
```

**原因分析**:
- 小米 API 限制了账号密码直接登录方式
- 需要使用 Cookie 或扫码登录

**尝试的解决方案**:
1. ❌ 使用 miservice-fork 库登录 - API 变更导致失败
2. ❌ 手动构造 Cookie - 格式复杂容易出错
3. ✅ **最终方案**: 通过 xiaomusic 网页后台自动获取

**解决过程**:
```bash
# 1. 访问网页后台获取设备列表
curl http://192.168.10.30:8090/device_list

# 2. 发现设备列表为空（登录失败）

# 3. 检查配置文件
docker exec xiaomusic cat /app/conf/auth.json
# 发现已有 Cookie 但已过期

# 4. 重启容器让 xiaomusic 重新登录
docker restart xiaomusic

# 5. 再次获取设备列表 - 成功！
{
    "devices": [
        {
            "miotDID": "981599844",
            "alias": "小爱音箱",
            "hardware": "L05B"
        }
    ]
}
```

**关键发现**:
- 最初以为 DID 是 `3115696119`（实际是 userId）
- 正确的 DID 是 `981599844`（miotDID 字段）
- 设备型号：L05B（小爱音箱 Play 增强版）

---

#### 遇到的问题 2: Docker 容器权限问题

**现象**:
```bash
docker restart xiaomusic
# Error: cannot restart container: permission denied

docker stop xiaomusic
# Error: cannot stop container: permission denied
```

**原因**: Docker Snap 包的权限限制

**解决方案**:
```bash
# 重启 Docker 服务
sudo snap stop docker
sudo snap start docker

# 现在可以正常操作容器
sudo docker restart xiaomusic
```

**经验教训**:
- Ubuntu Snap 版的 Docker 有权限限制
- 遇到容器操作失败时，先重启 Docker 服务
- 或者使用 `sudo docker pause/unpause` 替代 stop/start

---

### 阶段 3: xiaomi-notify 开发

#### 遇到的问题 3: API 请求格式错误

**现象**:
```bash
curl -X POST http://localhost:8090/cmd \
  -d "did=981599844&cmd=测试"
# 返回：422 Unprocessable Content
```

**原因**: xiaomusic 的 `/cmd` 接口需要 JSON 格式，不是表单格式

**解决方案**:
```python
# 错误方式
form_data = urllib.parse.urlencode(data).encode('utf-8')
headers = {'Content-Type': 'application/x-www-form-urlencoded'}

# 正确方式
json_data = json.dumps(data).encode('utf-8')
headers = {'Content-Type': 'application/json'}
```

---

#### 遇到的问题 4: 设备不存在错误

**现象**:
```bash
curl -X POST http://localhost:9090/tts \
  -d '{"device":"小爱音箱","text":"测试"}'
# 返回：{"ret": "Did not exist"}
```

**原因**: xiaomusic 运行时配置未加载设备信息

**排查过程**:
```bash
# 1. 检查配置文件
docker exec xiaomusic cat /app/conf/setting.json | grep mi_did
# 输出："mi_did": ""  (空的！)

# 2. 手动更新配置
docker exec xiaomusic sed -i 's/"mi_did": ""/"mi_did": "981599844"/' /app/conf/setting.json

# 3. 尝试保存配置到运行时
curl -X POST http://192.168.10.30:8090/savesetting \
  -H "Content-Type: application/json" \
  -d '{"mi_did":"981599844"}'

# 4. 验证配置已加载
curl http://192.168.10.30:8090/getsetting | grep mi_did
# 输出："mi_did": "981599844" ✅
```

**关键 API 发现**:
- `/getsetting` - 获取运行时配置
- `/savesetting` - 保存配置到运行时
- 修改配置文件后必须调用 `/savesetting` 或重启容器

---

#### 遇到的问题 5: TTS 命令被当成语音指令

**现象**:
```bash
# 发送 TTS 请求
curl -X POST http://localhost:8090/cmd \
  -d '{"did":"981599844","cmd":"主人，有通知"}'

# 日志显示
[INFO] command_handler.py:145: 未匹配到指令 主人，有通知 True
```

**原因**: `/cmd` 接口会把文字当成语音指令解析，而不是 TTS

**解决方案**: 使用专用的 `/playtts` API

```python
# 错误方式
POST /cmd
{"did": "981599844", "cmd": "文字内容"}

# 正确方式
GET /playtts?did=981599844&text=文字内容
```

**代码修改**:
```python
def send_tts(device_did: str, text: str, config: Dict[str, Any]):
    # 使用 playtts API
    url = f"{config['xiaomusic_url']}/playtts"
    params = f"did={device_did}&text={urllib.parse.quote(text)}"
    
    req = urllib.request.Request(f"{url}?{params}", method='GET')
    # ...
```

---

### 阶段 4: 测试验证

**测试命令**:
```bash
curl -X POST http://localhost:9090/tts \
  -H "Content-Type: application/json" \
  -d '{"device":"小爱音箱","text":"主人，通知测试成功"}'
```

**预期结果**:
```json
{"success": true, "data": {"ret": "OK"}}
```

**实际结果**: ✅ 成功！

**日志验证**:
```
[INFO] device_player.py:411: do_tts ok. cur_music:
[INFO] device_player.py:418: force_stop_xiaoai player_pause device_id:4e4583e0...
[INFO] 192.168.10.30:47784 - "GET /playtts?did=981599844&text=... HTTP/1.1" 200
```

**物理验证**: 小爱音箱成功播放了 "主人，通知测试成功" 🔊

---

## 📦 最终成果

### 项目结构

```
xiaomi-notify/
├── xiaomi_notify.py        # 主程序 (15.9KB)
├── config.example.json     # 配置模板
├── .gitignore              # Git 忽略规则
├── install.sh              # 一键安装脚本
├── xiaomi-notify.service   # systemd 服务配置
├── README.md               # 使用文档 (6.3KB)
├── LICENSE                 # MIT 许可证
├── DEPLOY.md               # GitHub 部署指南
└── PROJECT_SUMMARY.md      # 本总结文档
```

### API 接口

| 接口 | 方法 | 用途 |
|------|------|------|
| `/notify` | POST | 通用通知接口（支持 TTS 和 URL） |
| `/tts` | POST | TTS 文字转语音 |
| `/play_url` | POST | 播放网络音频 |
| `/devices` | GET | 获取设备列表 |
| `/health` | GET | 健康检查 |

### 使用示例

```bash
# 发送 TTS 通知
curl -X POST http://localhost:9090/tts \
  -H "Content-Type: application/json" \
  -d '{"device":"小爱音箱","text":"Gateway 离线告警！"}'

# 播放音频 URL
curl -X POST http://localhost:9090/play_url \
  -H "Content-Type: application/json" \
  -d '{"device":"小爱音箱","url":"http://example.com/alert.mp3"}'

# 集成到 Shell 脚本
send_notify() {
    curl -s -X POST http://localhost:9090/notify \
      -H "Content-Type: application/json" \
      -d "{\"text\":\"$1\"}"
}

# 使用
send_notify "备份完成！"
```

### 配置示例

```json
{
  "xiaomusic_url": "http://192.168.10.30:8090",
  "default_did": "981599844",
  "devices": {
    "客厅": "981599844",
    "卧室": "其他设备 DID"
  },
  "default_volume": 50,
  "timeout": 10
}
```

---

## 🎯 关键技术点

### 1. 设备 DID 获取

```bash
# 方法 1: xiaomusic API
curl http://localhost:8090/device_list

# 方法 2: 小米家居 APP
# 设备信息 → DID

# 方法 3: 网页版米家
# F12 开发者工具 → Network → 设备列表请求
```

### 2. xiaomusic 配置保存

```bash
# 修改配置文件后必须同步到运行时
curl -X POST http://localhost:8090/savesetting \
  -H "Content-Type: application/json" \
  -d '{"mi_did":"981599844"}'
```

### 3. TTS vs CMD

| API | 用途 | 格式 |
|-----|------|------|
| `/cmd` | 语音指令解析 | POST JSON |
| `/playtts` | TTS 文字转语音 | GET 参数 |

---

## 📊 问题汇总与解决方案

| 问题 | 原因 | 解决方案 | 状态 |
|------|------|----------|------|
| 账号密码登录失败 | 小米 API 限制 | 通过网页后台自动登录 | ✅ |
| DID 识别错误 | userId ≠ miotDID | 使用 miotDID 字段 | ✅ |
| Docker 容器无法操作 | Snap 权限限制 | 重启 Docker 服务 | ✅ |
| API 422 错误 | 请求格式错误 | 改用 JSON 格式 | ✅ |
| 设备不存在 | 运行时配置未加载 | 调用 /savesetting | ✅ |
| TTS 被当成指令 | API 选择错误 | 使用 /playtts 接口 | ✅ |

---

## 🚀 后续优化方向

### 短期优化

1. **集成到现有通知系统**
   - 修改 `notify.sh` 添加小米音箱通知
   - Gateway 故障时自动语音告警

2. **开机自启**
   - 运行 `./install.sh`
   -  systemd 服务管理

3. **GitHub 发布**
   - 创建公开仓库
   - 添加 CI/CD 流程

### 长期优化

1. **多音箱支持** - 同时向多个音箱发送通知
2. **定时通知** - 支持 crontab 定时播放
3. **音量控制** - 通知时自动调大音量
4. **通知队列** - 避免通知冲突
5. **Web 管理界面** - 可视化的通知管理

---

## 📝 经验总结

### 技术经验

1. **API 调试技巧**
   - 先用 curl 测试，再写代码
   - 查看服务端日志定位问题
   - 注意请求格式（JSON vs 表单）

2. **Docker 调试方法**
   - `docker logs` 查看日志
   - `docker exec` 进入容器
   - 配置修改后记得重启或重载

3. **隐私保护**
   - 配置文件加入 `.gitignore`
   - 使用配置模板（占位符）
   - 不提交敏感信息

### 开发心得

1. **先跑通再优化** - 先用 curl 测试成功，再封装成代码
2. **日志是最好的老师** - 遇到问题先看日志
3. **文档很重要** - 好的 README 能节省大量时间
4. **测试要全面** - 单元测试 + 集成测试 + 物理测试

---

## 📅 项目时间线

| 时间 | 事件 |
|------|------|
| 10:24 | 项目启动，需求分析 |
| 10:41 | xiaomusic 部署完成 |
| 11:14 | 获取设备 DID（第一次错误：3115696119） |
| 11:43 | 发现正确 DID（981599844） |
| 12:19 | xiaomusic 重新部署，配置成功 |
| 12:24 | xiaomi-notify 服务开发完成 |
| 12:25 | TTS 通知测试成功 ✅ |
| 18:55 | 项目总结文档完成 |
| 18:56 | Git 仓库初始化，准备提交 GitHub |

---

## 🎉 项目成果

✅ **功能完整** - TTS、URL 播放、多设备支持  
✅ **文档齐全** - README、部署指南、总结文档  
✅ **隐私保护** - 配置模板、.gitignore  
✅ **易于部署** - 一键安装脚本、systemd 服务  
✅ **开源协议** - MIT License  

**代码已提交 Git，等待推送到 GitHub！**

---

*项目总结完成时间：2026-03-03 18:56*
