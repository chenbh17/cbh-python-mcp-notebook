#!/bin/bash
# 优化版MCP容器启动脚本
# 解决容器运行时长-t设置多久,返回python mcp服务器启动信息就要多久的问题

# 默认参数
CPU_COUNT=1
MEMORY_LIMIT="1g"
STORAGE_LIMIT="10g"
GPU_MEMORY=""
STREAMABLE_HTTP=true
TIMEOUT=3600  # 1小时默认超时
PORT=7000  # 默认MCP端口
NOTEBOOK_PORT=7777  # 默认Notebook端口
DOWNLOAD_PORT=777  # 默认下载端口
ENABLE_NOTEBOOK=true  # 默认启用Notebook
CONTAINER_NAME_PREFIX="python-mcp-container"
EXTERNAL_HOST="localhost"  # 默认外部主机名
INCLUDE_PORT=""  # 端口包含控制，空字符串表示自动判断

# 帮助信息
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -c, --cpu COUNT        CPU核心数限制 (默认: 1)"
    echo "  -m, --memory SIZE      内存限制 (默认: 1g)"
    echo "  -s, --storage SIZE     存储空间限制提示信息 (注意: 实际限制取决于Docker存储驱动)"
    echo "  -g, --gpu-memory SIZE  GPU显存限制 (可选)"
    echo "  -p, --port PORT        指定MCP端口号 (默认: 7000)"
    echo "  -n, --notebook-port PORT  指定Notebook端口号 (默认: 7777)"
    echo "  -d, --download-port PORT  指定下载端口号 (默认: 777)"
    echo "  -t, --timeout SECONDS  运行时长限制(秒) (默认: 3600)"
    echo "  --streamable-http      启用Streamable HTTP模式 (默认: false)"
    echo "  --notebook             启用Jupyter Notebook服务 (默认: true)"
    echo "  --external-host HOST   指定外部访问主机名/IP (默认: localhost)"
    echo "  --include-port BOOL    是否包含端口 (true/false/auto) (默认: auto)"
    echo "  --no-timeout           不设置自动超时 (容器将一直运行直到手动停止)"
    echo "  -h, --help             显示帮助信息"
    exit 1
}

# 解析命令行参数
NO_TIMEOUT=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--cpu)
            CPU_COUNT="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY_LIMIT="$2"
            shift 2
            ;;
        -s|--storage)
            STORAGE_LIMIT="$2"
            shift 2
            ;;
        -g|--gpu-memory)
            GPU_MEMORY="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -n|--notebook-port)
            NOTEBOOK_PORT="$2"
            shift 2
            ;;
        -d|--download-port)
            DOWNLOAD_PORT="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --streamable-http)
            STREAMABLE_HTTP=true
            shift 1
            ;;
        --notebook)
            ENABLE_NOTEBOOK=true
            shift 1
            ;;
        --external-host)
            EXTERNAL_HOST="$2"
            shift 2
            ;;
        --include-port)
            INCLUDE_PORT="$2"
            shift 2
            ;;
        --no-timeout)
            NO_TIMEOUT=true
            shift 1
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option $1"
            usage
            ;;
    esac
done

# 生成唯一的容器ID
CONTAINER_ID=$(openssl rand -hex 8)
CONTAINER_NAME="${CONTAINER_NAME_PREFIX}-${CONTAINER_ID}"

# 在当前目录下创建挂载目录
MOUNT_DIR="$(pwd)/${CONTAINER_NAME}"
mkdir -p "${MOUNT_DIR}"

# 检查端口是否被占用，如果被占用则尝试下一个端口
check_port() {
    local port=$1
    while netstat -tuln | grep -q ":$port "; do
        echo "Port $port is occupied, trying port $((port + 1))..."
        port=$((port + 1))
    done
    echo $port
}

# 获取可用端口
PORT_OUTPUT=$(check_port $PORT 2>&1)
AVAILABLE_PORT=$(echo "$PORT_OUTPUT" | grep -o '[0-9]*$')

# 检查Notebook端口
if [ "$ENABLE_NOTEBOOK" = true ]; then
    NOTEBOOK_PORT_OUTPUT=$(check_port $NOTEBOOK_PORT 2>&1)
    AVAILABLE_NOTEBOOK_PORT=$(echo "$NOTEBOOK_PORT_OUTPUT" | grep -o '[0-9]*$')
fi

# 检查下载端口
DOWNLOAD_PORT_OUTPUT=$(check_port $DOWNLOAD_PORT 2>&1)
AVAILABLE_DOWNLOAD_PORT=$(echo "$DOWNLOAD_PORT_OUTPUT" | grep -o '[0-9]*$')

echo "Creating container with ID: ${CONTAINER_ID}"
echo "Mount directory: ${MOUNT_DIR}"
echo "CPU limit: ${CPU_COUNT} cores"
echo "Memory limit: ${MEMORY_LIMIT}"
echo "Storage limit (informational): ${STORAGE_LIMIT}"
echo "MCP Port: ${AVAILABLE_PORT}"
if [ "$ENABLE_NOTEBOOK" = true ]; then
    echo "Notebook Port: ${AVAILABLE_NOTEBOOK_PORT}"
fi
echo "Download Port: ${AVAILABLE_DOWNLOAD_PORT}"
echo "Streamable HTTP mode: ${STREAMABLE_HTTP}"
if [ "$NO_TIMEOUT" = true ]; then
    echo "Timeout: No timeout (container will run indefinitely)"
else
    echo "Timeout: ${TIMEOUT} seconds"
fi

# 检查Docker镜像是否存在
# 统一使用notebook版本的镜像
IMAGE_NAME="python-mcp-server-notebook:latest"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo "Docker image ${IMAGE_NAME} not found. Please build the image first."
    exit 1
fi

# 构建Docker运行参数
DOCKER_RUN_ARGS=(
    "--name=${CONTAINER_NAME}"
    "--restart=unless-stopped"
    "--cpus=${CPU_COUNT}"
    "--memory=${MEMORY_LIMIT}"
    "--mount=type=bind,source=${MOUNT_DIR},target=/workspace"
    "-p=${AVAILABLE_PORT}:7000"
    "-d"  # 后台运行
    "-e" "CONTAINER_TIMEOUT=${TIMEOUT}"  # 传递超时设置作为环境变量
    "-e" "CONTAINER_ID=${CONTAINER_ID}"  # 传递容器ID作为环境变量
    "-e" "EXTERNAL_HOST=${EXTERNAL_HOST}"  # 传递外部主机名作为环境变量
)

# 添加端口控制环境变量
if [ -n "$INCLUDE_PORT" ]; then
    DOCKER_RUN_ARGS+=("-e" "INCLUDE_PORT=${INCLUDE_PORT}")
fi

# 如果启用了Notebook，添加Notebook端口映射
if [ "$ENABLE_NOTEBOOK" = true ]; then
    DOCKER_RUN_ARGS+=("-p=${AVAILABLE_NOTEBOOK_PORT}:7777")
fi

# 添加下载端口映射
DOCKER_RUN_ARGS+=("-p=${AVAILABLE_DOWNLOAD_PORT}:777")

# 如果指定了GPU内存，则添加相关参数
if [ -n "$GPU_MEMORY" ]; then
    # 检查NVIDIA容器工具包是否可用
    if command -v nvidia-smi &> /dev/null; then
        # 使用NVIDIA运行时
        DOCKER_RUN_ARGS+=("--gpus=all")
        # 通过环境变量传递GPU内存限制信息
        DOCKER_RUN_ARGS+=("-e GPU_MEMORY_LIMIT=${GPU_MEMORY}")
        echo "GPU enabled with memory limit setting: ${GPU_MEMORY}"
        echo "Note: Actual GPU memory enforcement depends on application-level configuration"
    else
        echo "Warning: NVIDIA tools not found. GPU limitations may not be enforced."
        DOCKER_RUN_ARGS+=("--gpus=all")
    fi
fi

# 启动容器
echo "Starting container..."
if [ "$STREAMABLE_HTTP" = true ] && [ "$ENABLE_NOTEBOOK" = true ]; then
    # 同时启用Notebook和Streamable HTTP模式
    echo "Starting with both Streamable HTTP and Jupyter Notebook enabled..."
    docker run "${DOCKER_RUN_ARGS[@]}" "${IMAGE_NAME}" bash -c "
        # 启动 Streamable HTTP MCP 服务
        python /app/mcp_server.py streamable &
        MCP_PID=\$!
        sleep 3 &&
        # 启动 Jupyter Notebook
        jupyter notebook --allow-root --ip=0.0.0.0 --port=7777 --no-browser --notebook-dir=/workspace --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.allow_origin='*' --NotebookApp.disable_check_xsrf=True &
        JUPYTER_PID=\$!
        echo \"Streamable MCP PID: \$MCP_PID\"
        echo \"Jupyter PID: \$JUPYTER_PID\"
        # 等待两个进程都退出
        wait \$MCP_PID
        wait \$JUPYTER_PID
    "
elif [ "$ENABLE_NOTEBOOK" = true ]; then
    # 仅启用Notebook模式，不运行streamable-http
    echo "Starting with Jupyter Notebook enabled (traditional MCP mode)..."
    docker run "${DOCKER_RUN_ARGS[@]}" "${IMAGE_NAME}" bash -c "
        python /app/mcp_server.py &
        MCP_PID=\$!
        sleep 3 &&
        jupyter notebook --allow-root --ip=0.0.0.0 --port=7777 --no-browser --notebook-dir=/workspace --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.allow_origin='*' --NotebookApp.disable_check_xsrf=True &
        JUPYTER_PID=\$!
        echo \"MCP PID: \$MCP_PID\"
        echo \"Jupyter PID: \$JUPYTER_PID\"
        wait \$MCP_PID
        wait \$JUPYTER_PID
    "
elif [ "$STREAMABLE_HTTP" = true ]; then
    # 仅启用Streamable HTTP模式，不运行notebook
    echo "Starting in Streamable HTTP mode only..."
    docker run "${DOCKER_RUN_ARGS[@]}" "${IMAGE_NAME}" bash -c "
        python /app/mcp_server.py streamable &
        MCP_PID=\$!
        echo \"Streamable MCP PID: \$MCP_PID\"
        wait \$MCP_PID
    "
else
    echo "Starting in traditional mode..."
    docker run "${DOCKER_RUN_ARGS[@]}" "${IMAGE_NAME}" bash -c "
        # 启动MCP服务和Nginx代理
        /app/start_services_with_proxy.sh
    "
fi

# 检查容器是否成功启动
if [ $? -eq 0 ]; then
    echo "Container started successfully!"
    echo "Container name: ${CONTAINER_NAME}"
    echo "Access Download endpoint at: http://localhost:${AVAILABLE_DOWNLOAD_PORT}/download/"
    echo "Access Download via Nginx Proxy at: http://localhost:70/${CONTAINER_ID}/download/"
    if [ "$STREAMABLE_HTTP" = true ] && [ "$ENABLE_NOTEBOOK" = true ]; then
        echo "Access Streamable HTTP endpoint at: http://localhost:${AVAILABLE_PORT}/mcp"
        echo "Use proper JSON-RPC headers: Accept: application/json, text/event-stream"
        echo "Access Jupyter Notebook at: http://localhost:${AVAILABLE_NOTEBOOK_PORT}"
        echo "Access Jupyter Notebook via Nginx Proxy at: http://localhost:70/${CONTAINER_ID}/notebook"
    elif [ "$ENABLE_NOTEBOOK" = true ]; then
        echo "Access traditional API endpoint at: http://localhost:${AVAILABLE_PORT}"
        echo "Access Jupyter Notebook at: http://localhost:${AVAILABLE_NOTEBOOK_PORT}"
        echo "Access Jupyter Notebook via Nginx Proxy at: http://localhost:70/${CONTAINER_ID}/notebook"
    elif [ "$STREAMABLE_HTTP" = true ]; then
        echo "Access Streamable HTTP endpoint at: http://localhost:${AVAILABLE_PORT}/mcp"
        echo "Use proper JSON-RPC headers: Accept: application/json, text/event-stream"
    else
        echo "Access traditional API endpoint at: http://localhost:${AVAILABLE_PORT}"
    fi
    
    # 设置超时自动关闭（在后台运行，不阻塞当前脚本）
    if [ "$NO_TIMEOUT" = false ]; then
        {
            sleep ${TIMEOUT}
            echo "Timeout reached, stopping container..."
            if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
                docker stop ${CONTAINER_NAME} >/dev/null 2>&1
                echo "Container stopped."
            fi
        } &
        echo "Container timeout process started in background (PID: $!)."
        echo "Container will auto-stop in ${TIMEOUT} seconds"
    else
        echo "Container will run indefinitely (no timeout set)"
    fi
    
    # 触发Nginx代理更新
    echo "Updating Nginx proxy configuration..."
    /home/chenbh17/anaconda3/bin/python3 /media/chenbh17/cbhssd/python-mcp-notebook/manage_nginx_proxy.py
    
    echo "To stop manually, run: docker stop ${CONTAINER_NAME}"
    
    # 立即退出，不等待超时
    exit 0
else
    echo "Failed to start container"
    exit 1
fi