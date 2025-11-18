# Mastodon News Center 生产环境部署指南

本指南将帮助你将 Mastodon News Center 部署到生产服务器上。

## 前置要求

### 服务器要求

- **操作系统**：Ubuntu 20.04+ / Debian 11+ / CentOS 8+（推荐 Ubuntu 22.04 LTS）
- **内存**：至少 2GB RAM（推荐 4GB+）
- **存储**：至少 20GB 可用空间
- **CPU**：至少 1 核心（推荐 2 核心+）

### 软件要求

- **Docker**：20.10+
- **Docker Compose**：2.0+
- **Nginx**：1.18+（用于反向代理和 HTTPS）
- **域名**：一个已解析到服务器 IP 的域名（可选，但推荐）

## 部署步骤

### 1. 服务器准备

#### 1.1 连接到服务器

```bash
ssh root@your-server-ip
```

#### 1.2 更新系统

```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

#### 1.3 安装 Docker 和 Docker Compose

**Ubuntu/Debian：**

```bash
# 安装必要的依赖
apt install -y curl git

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 启动 Docker 服务
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
apt install -y docker-compose

# 或者使用 Docker Compose V2（推荐）
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

**CentOS/RHEL：**

```bash
# 安装 Docker
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

验证安装：

```bash
docker --version
docker-compose --version
```

### 2. 部署应用

#### 2.1 克隆项目

```bash
# 创建应用目录
mkdir -p /opt/mastodon-news-center
cd /opt/mastodon-news-center

# 克隆项目（替换为你的仓库地址）
git clone https://github.com/yourusername/mastodon-news-center.git .

# 或者使用 HTTPS
git clone https://github.com/somincola/mastodon-news-center.git .
```

#### 2.2 创建环境变量文件

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

**⚠️ 重要：必须修改以下配置项！**

```env
# ============================================
# 数据库配置（必须修改密码！）
# ============================================
POSTGRES_USER=mastodon_news
# ⚠️ 生产环境必须使用强密码（至少 16 位，包含大小写字母、数字、特殊字符）
POSTGRES_PASSWORD=Your_Strong_Password_123!@#
POSTGRES_DB=mastodon_news
POSTGRES_PORT=5432

# ============================================
# 应用配置
# ============================================
APP_PORT=8000

# ============================================
# Mastodon 配置
# ============================================
# 替换为你的 Mastodon 实例地址
MASTODON_BASE_URL=https://m.somincola.org
# Mastodon 帖子最大字符数（默认 500）
MASTODON_MAX_LENGTH=500

# ============================================
# OpenAI 配置（可选）
# ============================================
# 如需使用 AI 摘要功能，填写你的 OpenAI API Key
OPENAI_API_KEY=sk-...

# ============================================
# 数据库连接字符串（会自动根据上面的配置生成）
# ============================================
DATABASE_URL=postgresql://mastodon_news:Your_Strong_Password_123!@#@db:5432/mastodon_news
```

**生成强密码的方法：**

```bash
# 使用 openssl 生成随机密码
openssl rand -base64 32

# 或者使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2.3 设置文件权限

```bash
# 确保 .env 文件权限安全
chmod 600 .env

# 创建日志目录
mkdir -p logs
chmod 755 logs
```

#### 2.4 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 2.5 验证服务运行

```bash
# 检查容器状态（应该都是 "Up" 状态）
docker-compose ps

# 检查应用日志（确认没有错误）
docker-compose logs app

# 检查数据库日志
docker-compose logs db

# 测试应用是否可访问（从服务器本地测试）
curl http://localhost:8000
```

### 3. 配置 Nginx 反向代理

#### 3.1 安装 Nginx

```bash
# Ubuntu/Debian
apt install -y nginx

# CentOS/RHEL
yum install -y nginx

# 启动 Nginx
systemctl start nginx
systemctl enable nginx
```

#### 3.2 创建 Nginx 配置文件

```bash
# 创建配置文件
nano /etc/nginx/sites-available/mastodon-news-center
```

**如果没有 `/etc/nginx/sites-available` 目录（CentOS），创建它：**

```bash
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled
```

在 `nginx.conf` 的 `http` 块中添加：

```nginx
include /etc/nginx/sites-enabled/*;
```

**配置文件内容（HTTP 版本）：**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    # 客户端最大请求体大小（用于上传配置等）
    client_max_body_size 10M;

    # 代理到应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location /static/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 日志
    access_log /var/log/nginx/mastodon-news-center.access.log;
    error_log /var/log/nginx/mastodon-news-center.error.log;
}
```

**启用配置：**

```bash
# Ubuntu/Debian
ln -s /etc/nginx/sites-available/mastodon-news-center /etc/nginx/sites-enabled/

# CentOS（如果使用 sites-enabled）
ln -s /etc/nginx/sites-available/mastodon-news-center /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重载 Nginx
systemctl reload nginx
```

### 4. 配置 HTTPS（使用 Let's Encrypt）

#### 4.1 安装 Certbot

```bash
# Ubuntu/Debian
apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
yum install -y certbot python3-certbot-nginx
```

#### 4.2 获取 SSL 证书

```bash
# 确保域名已解析到服务器 IP
# 运行以下命令获取证书
certbot --nginx -d your-domain.com

# 或者交互式运行
certbot certonly --nginx -d your-domain.com
```

Certbot 会自动：
- 获取 SSL 证书
- 配置 Nginx 使用 HTTPS
- 设置自动续期

#### 4.3 验证自动续期

```bash
# 测试自动续期
certbot renew --dry-run

# 查看证书状态
certbot certificates
```

#### 4.4 更新 Nginx 配置（如果需要手动配置 HTTPS）

如果 Certbot 没有自动配置，手动更新配置文件：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向 HTTP 到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书路径
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 配置（安全最佳实践）
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS（可选，但推荐）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    access_log /var/log/nginx/mastodon-news-center.access.log;
    error_log /var/log/nginx/mastodon-news-center.error.log;
}
```

### 5. 防火墙配置

#### 5.1 Ubuntu/Debian（UFW）

```bash
# 安装 UFW
apt install -y ufw

# 允许 SSH（重要！先允许 SSH）
ufw allow 22/tcp

# 允许 HTTP 和 HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# 启动防火墙
ufw enable

# 查看状态
ufw status
```

#### 5.2 CentOS/RHEL（firewalld）

```bash
# 启动 firewalld
systemctl start firewalld
systemctl enable firewalld

# 允许 HTTP 和 HTTPS
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# 允许 SSH（如果还没有）
firewall-cmd --permanent --add-service=ssh

# 重载配置
firewall-cmd --reload

# 查看状态
firewall-cmd --list-all
```

**⚠️ 重要**：
- **不要**在防火墙中开放 8000 端口（应用端口）
- 只开放 80（HTTP）和 443（HTTPS）端口
- 确保 SSH 端口（通常是 22）已开放，否则可能无法远程连接

### 6. 配置自动启动

#### 6.1 确保 Docker 自动启动

```bash
# 检查 Docker 服务状态
systemctl status docker

# 确保 Docker 开机自启（应该已经启用）
systemctl enable docker
```

#### 6.2 创建启动脚本（可选）

```bash
# 创建启动脚本
nano /opt/mastodon-news-center/start.sh
```

脚本内容：

```bash
#!/bin/bash
cd /opt/mastodon-news-center
docker-compose up -d
```

```bash
# 设置执行权限
chmod +x /opt/mastodon-news-center/start.sh
```

#### 6.3 创建 systemd 服务（推荐）

```bash
# 创建服务文件
nano /etc/systemd/system/mastodon-news-center.service
```

服务文件内容：

```ini
[Unit]
Description=Mastodon News Center
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/mastodon-news-center
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
# 重载 systemd
systemctl daemon-reload

# 启用服务
systemctl enable mastodon-news-center

# 启动服务
systemctl start mastodon-news-center

# 查看状态
systemctl status mastodon-news-center
```

### 7. 备份配置

#### 7.1 创建备份脚本

```bash
# 创建备份目录
mkdir -p /opt/backups/mastodon-news-center

# 创建备份脚本
nano /opt/mastodon-news-center/backup.sh
```

备份脚本内容：

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/mastodon-news-center"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cd /opt/mastodon-news-center
docker-compose exec -T db pg_dump -U mastodon_news mastodon_news > $BACKUP_DIR/db_backup_$DATE.sql

# 备份配置文件（不包含敏感信息）
tar -czf $BACKUP_FILE \
    --exclude='.env' \
    --exclude='logs/*' \
    --exclude='*.log' \
    /opt/mastodon-news-center

# 压缩数据库备份
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 删除 30 天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_FILE"
```

```bash
# 设置执行权限
chmod +x /opt/mastodon-news-center/backup.sh

# 测试运行
/opt/mastodon-news-center/backup.sh
```

#### 7.2 配置自动备份（Cron）

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点执行备份
0 2 * * * /opt/mastodon-news-center/backup.sh >> /var/log/mastodon-news-center-backup.log 2>&1
```

### 8. 监控和维护

#### 8.1 查看服务状态

```bash
# 查看容器状态
cd /opt/mastodon-news-center
docker-compose ps

# 查看应用日志
docker-compose logs -f app

# 查看数据库日志
docker-compose logs -f db

# 查看所有服务日志
docker-compose logs -f
```

#### 8.2 重启服务

```bash
cd /opt/mastodon-news-center

# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart app
docker-compose restart db

# 完全重启（停止后重新启动）
docker-compose down
docker-compose up -d
```

#### 8.3 更新应用

```bash
cd /opt/mastodon-news-center

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose build --no-cache
docker-compose up -d

# 查看日志确认更新成功
docker-compose logs -f app
```

#### 8.4 查看资源使用

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看 Docker 磁盘使用
docker system df
```

### 9. 安全建议

#### 9.1 定期更新

```bash
# 更新系统
apt update && apt upgrade -y  # Ubuntu/Debian
yum update -y                  # CentOS/RHEL

# 更新 Docker 镜像
cd /opt/mastodon-news-center
docker-compose pull
docker-compose up -d
```

#### 9.2 限制数据库访问

确保 `docker-compose.yml` 中数据库端口只在容器内部访问（默认配置已正确）：

```yaml
ports:
  - "127.0.0.1:5432:5432"  # 只在本地访问，不对外暴露
```

#### 9.3 定期备份

确保备份脚本正常运行，定期检查备份文件。

#### 9.4 监控日志

定期检查应用日志，及时发现异常：

```bash
# 查看错误日志
docker-compose logs app | grep ERROR

# 查看最近的日志
docker-compose logs --tail=100 app
```

### 10. 故障排除

#### 10.1 应用无法访问

1. **检查容器状态**：
   ```bash
   docker-compose ps
   ```

2. **检查应用日志**：
   ```bash
   docker-compose logs app
   ```

3. **检查 Nginx 配置**：
   ```bash
   nginx -t
   systemctl status nginx
   ```

4. **检查防火墙**：
   ```bash
   ufw status          # Ubuntu/Debian
   firewall-cmd --list-all  # CentOS/RHEL
   ```

#### 10.2 数据库连接失败

1. **检查数据库容器状态**：
   ```bash
   docker-compose ps db
   docker-compose logs db
   ```

2. **检查环境变量**：
   ```bash
   docker-compose exec app env | grep DATABASE_URL
   ```

3. **测试数据库连接**：
   ```bash
   docker-compose exec db psql -U mastodon_news -d mastodon_news
   ```

#### 10.3 SSL 证书问题

1. **检查证书状态**：
   ```bash
   certbot certificates
   ```

2. **手动续期证书**：
   ```bash
   certbot renew
   ```

3. **测试自动续期**：
   ```bash
   certbot renew --dry-run
   ```

## 部署检查清单

在完成部署后，请确认以下项目：

- [ ] 所有容器正常运行（`docker-compose ps`）
- [ ] 应用可以正常访问（通过域名）
- [ ] HTTPS 配置正确（证书有效）
- [ ] 防火墙已配置（只开放必要端口）
- [ ] 数据库密码已修改为强密码
- [ ] 备份脚本已配置并测试
- [ ] 自动启动已配置
- [ ] 日志文件正常生成
- [ ] 可以通过 Web 界面访问管理后台
- [ ] 可以创建 Bot 并配置 RSS 源
- [ ] 定时任务正常运行

## 访问应用

部署完成后，访问以下地址：

- **Web 管理界面**：https://your-domain.com/admin
- **API 文档**：https://your-domain.com/docs

## 后续支持

如有问题，请查看：
- 项目 README.md
- 故障排除部分
- GitHub Issues

祝你部署顺利！🎉

