#!/bin/bash
# 启动MCP服务和Nginx代理

# 启动MCP服务器 (Streamable HTTP 模式)
echo "Starting Streamable HTTP MCP server..."
python /app/mcp_server.py streamable &
MCP_PID=$!

# 等待 Streamable 完全启动
sleep 3

# 启动Nginx代理
echo "Starting Nginx proxy..."
/app/nginx_proxy_runner.sh &
NGINX_PROXY_PID=$!

echo "Streamable MCP PID: $MCP_PID"
echo "Nginx Proxy PID: $NGINX_PROXY_PID"

# 等待所有进程都退出
wait $MCP_PID
wait $NGINX_PROXY_PID