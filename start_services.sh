#!/bin/bash

# 启动 Streamable HTTP MCP 服务
echo "Starting Streamable HTTP MCP server..."
python /app/mcp_server.py streamable &
MCP_PID=$!

# 等待 Streamable 完全启动
sleep 3

# 启动 Jupyter Notebook
echo "Starting Jupyter Notebook..."
jupyter lab --allow-root --ServerApp.ip=0.0.0.0 --ServerApp.port=7777 --ServerApp.token='' --ServerApp.password='' --ServerApp.root_dir=/workspace --ServerApp.allow_origin='*' --ServerApp.disable_check_xsrf=True --ServerApp.open_browser=False &
JUPYTER_PID=$!

echo "Streamable MCP PID: $MCP_PID"
echo "Jupyter PID: $JUPYTER_PID"

# 等待两个进程都退出（任一退出不会终止另一个）
wait $MCP_PID
wait $JUPYTER_PID