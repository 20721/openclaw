# 部署到 GitHub 指南

## 方法 1: 使用 HTTPS（推荐新手）

### 1. 在 GitHub 创建新仓库

访问 https://github.com/new，创建名为 `xiaomi-notify` 的仓库。

### 2. 添加远程仓库

```bash
cd ~/.openclaw/workspace/tools/xiaomi-notify

# 替换 YOUR_USERNAME 为你的 GitHub 用户名
git remote add origin https://github.com/YOUR_USERNAME/xiaomi-notify.git
```

### 3. 推送代码

```bash
git branch -M main
git push -u origin main
```

首次推送时需要输入 GitHub 用户名和密码（或个人访问令牌）。

---

## 方法 2: 使用 SSH（推荐）

### 1. 生成 SSH 密钥

```bash
ssh-keygen -t ed25519 -C "pzxsky@gmail.com" -f ~/.ssh/github_ed25519
```

### 2. 添加 SSH 密钥到 GitHub

```bash
# 复制公钥
cat ~/.ssh/github_ed25519.pub

# 访问 https://github.com/settings/keys
# 点击 "New SSH key"，粘贴公钥内容
```

### 3. 配置 SSH

```bash
# 创建 SSH 配置
cat >> ~/.ssh/config << EOF

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_ed25519
EOF

chmod 600 ~/.ssh/config
```

### 4. 添加远程仓库并推送

```bash
cd ~/.openclaw/workspace/tools/xiaomi-notify

# 替换 YOUR_USERNAME 为你的 GitHub 用户名
git remote add origin git@github.com:YOUR_USERNAME/xiaomi-notify.git

git branch -M main
git push -u origin main
```

---

## 方法 3: 使用 GitHub CLI（最方便）

### 1. 安装 GitHub CLI

```bash
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# 验证安装
gh --version
```

### 2. 登录 GitHub

```bash
gh auth login
# 按提示选择 GitHub.com -> HTTPS -> 登录浏览器
```

### 3. 创建仓库并推送

```bash
cd ~/.openclaw/workspace/tools/xiaomi-notify

# 创建仓库并推送
gh repo create xiaomi-notify --public --source=. --remote=origin --push
```

---

## 验证推送

推送成功后，访问你的 GitHub 仓库页面确认文件已上传：

```
https://github.com/YOUR_USERNAME/xiaomi-notify
```

---

## 后续更新

代码修改后，提交并推送更新：

```bash
cd ~/.openclaw/workspace/tools/xiaomi-notify

# 提交更改
git add .
git commit -m "feat: 更新说明"

# 推送到 GitHub
git push
```

---

## 注意事项

1. **隐私信息**: `config.json` 已在 `.gitignore` 中，不会被提交
2. **许可证**: 项目使用 MIT License，详见 `LICENSE` 文件
3. **文档**: 确保 `README.md` 清晰完整
