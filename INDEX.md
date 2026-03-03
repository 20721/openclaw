# OpenClaw 项目索引

> 所有 OpenClaw 相关项目的索引和链接

---

## 📋 索引说明

本索引记录所有已开发/部署的 OpenClaw 项目，包括：
- **项目名称**: 项目的唯一标识
- **作用**: 项目的主要功能
- **状态**: 开发进度
- **群晖路径**: NAS 上的备份位置
- **GitHub 链接**: 项目源代码仓库
- **备份时间**: 首次备份到群晖的时间

---

## 📁 项目列表

### 🚨 通知系统

| 项目名称 | 作用 | 状态 | 群晖路径 | GitHub 链接 | 备份时间 |
|----------|------|------|----------|-------------|----------|
| notify-xiaomi | 小米音箱通知服务 - 通过 xiaomusic 控制小米音箱播放通知 | ✅ 已完成 | /openclaw/2026-03-03/xiaomi-notify | https://github.com/20721/xiaomi-notify | 2026-03-03 |

### 💾 备份系统

| 项目名称 | 作用 | 状态 | 群晖路径 | GitHub 链接 | 备份时间 |
|----------|------|------|----------|-------------|----------|
| backup-system | OpenClaw 灾难恢复系统 - 完整备份和一键恢复解决方案 | ✅ 已完成 | /openclaw/2026-03-03/backup-system | https://github.com/20721/openclaw-backup-system | 2026-03-03 |

### 📊 监控系统

| 项目名称 | 作用 | 状态 | 群晖路径 | GitHub 链接 | 备份时间 |
|----------|------|------|----------|-------------|----------|
| monitor-gateway | Gateway 健康监控 - 每 5 分钟检查 Gateway 状态 | ✅ 已完成 | /openclaw/2026-03-02/monitor-gateway | - | 2026-03-02 |

### 🎯 技能

| 项目名称 | 作用 | 状态 | 群晖路径 | GitHub 链接 | 备份时间 |
|----------|------|------|----------|-------------|----------|
| skill-memory | 记忆隔离系统 - 智能记忆管理 | ✅ 已完成 | - | - | - |

---

## 🗂️ 群晖目录结构

```
/openclaw/
├── INDEX.md                        # 总索引文件（本文件）
├── 2026-03-02/                     # 日期目录
│   └── monitor-gateway/            # 项目文件夹
├── 2026-03-03/                     # 日期目录
│   ├── backup-system/              # 项目文件夹
│   └── xiaomi-notify/              # 项目文件夹
└── 2026-03-04/                     # 新日期目录
    └── ...
```

---

## 🔗 GitHub 目录结构

```
github.com/20721/openclaw/          # 主仓库（索引）
├── README.md                       # 总说明
├── INDEX.md                        # 项目索引（本文件）
└── backup-system/                  # 项目子模块（已废弃，使用独立仓库）

github.com/20721/openclaw-backup-system/  # 独立项目仓库
└── ...（项目文件）

github.com/20721/xiaomi-notify/     # 独立项目仓库
└── ...（项目文件）
```

---

## 📝 更新记录

| 日期 | 操作 | 项目名称 | 说明 |
|------|------|----------|------|
| 2026-03-03 | 新增 | backup-system | OpenClaw 灾难恢复系统 v2.0 |
| 2026-03-03 | 新增 | notify-xiaomi | 小米音箱通知服务 |
| 2026-03-02 | 新增 | monitor-gateway | Gateway 健康监控 |

---

## 🔍 快速查找

### 按功能查找
- **备份恢复**: backup-system
- **通知告警**: notify-xiaomi, notify-gateway
- **监控检查**: monitor-gateway, monitor-health
- **技能扩展**: skill-weather, skill-github, skill-memory

### 按状态查找
- **✅ 已完成**: backup-system, notify-xiaomi, monitor-gateway
- **🚧 开发中**: backup-nas, notify-gateway, monitor-health

---

*最后更新：2026-03-03*
