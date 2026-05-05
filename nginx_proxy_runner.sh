#!/bin/bash
# Nginx反向代理Docker容器的脚本

# 创建Nginx配置目录
mkdir -p /etc/nginx/conf.d

# 启动Nginx
echo "Starting Nginx proxy server..."
nginx -g "daemon off;" &

# 等待Nginx启动
sleep 2

# 初始配置更新
echo "Updating proxy configuration..."
python3 /app/update_nginx_proxy.py

# 定期更新配置（每10秒检查一次）
while true; do
    sleep 10
    python3 /app/update_nginx_proxy.py
done