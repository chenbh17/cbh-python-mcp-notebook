# Python MCP Server


这是一个基于Docker的Python MCP（Model Container Protocol）服务器，允许远程执行Python代码和安装依赖包。

## 功能特性

1. **代码执行**：通过HTTP API远程执行Python代码
2. **依赖管理**：动态安装Python包
3. **资源限制**：
   - CPU核心数限制
   - 内存限制
   - GPU显存限制
   - 存储空间限制
   - 运行时间限制
4. **隔离环境**：每个容器实例都有独立的工作区目录
5. **自动清理**：容器超时后自动停止
6. **预装依赖**：包含常用的数据科学和机器学习库

## 预装依赖包

容器镜像默认包含以下Python包，可直接使用无需安装：

- **深度学习框架**：torch, tensorflow, keras
- **数据处理**：pandas, numpy, openpyxl
- **数据库连接**：pymysql, pyhive, clickhouse_connect
- **机器学习**：lightgbm, xgboost, scikit-optimize, statsmodels
- **文本处理**：jieba
- **工具库**：tqdm, joblib, Pillow
- **网络通信**：paramiko, thrift, thrift_sasl
- **数据可视化**：matplotlib, seaborn

这些包已经预装在容器中，可以直接导入使用，无需额外安装时间。

## 使用方法

### 启动容器

```bash
# 给脚本添加执行权限
chmod +x start_mcp_container.sh

# 启动容器（默认参数）
./start_mcp_container.sh

# 启动容器（自定义参数）
./start_mcp_container.sh -c 2 -m 4g -t 3600

# 启动容器（带GPU显存限制）
./start_mcp_container.sh -c 2 -m 4g -g 2g -t 3600

# 启动支持Streamable HTTP的容器
./start_mcp_container.sh --streamable-http -c 2 -m 2g -t 3600

# 启动支持Streamable HTTP和GPU的容器
./start_mcp_container.sh --streamable-http -c 2 -m 4g -g 2g -t 3600

# 启动带Jupyter Notebook的容器
./start_mcp_container.sh --notebook -c 2 -m 4g -t 3600

# 启动同时带Streamable HTTP和Notebook的容器
./start_mcp_container.sh --streamable-http --notebook -c 2 -m 4g -t 3600

#综合
./start_mcp_container.sh --streamable-http --notebook --external-host chenbh17-python-mcp.iepose.cn --include-port false -c 24 -m 192g -g 32g -s 10000g -t 36000000000
./start_mcp_container.sh --streamable-http --notebook --external-host 115.190.211.94 --include-port true -c 24 -m 192g -g 32g -s 10000g -t 36000000000
#前端启动指令
@reboot cd /media/chenbh17/cbhssd/python-mcp-notebook && nohup /home/chenbh17/anaconda3/bin/python /media/chenbh17/cbhssd/python-mcp-notebook/container_manager.py &
```

### 参数说明

- `-c, --cpu COUNT`：CPU核心数限制（默认：1）
- `-m, --memory SIZE`：内存限制（默认：1g）
- `-s, --storage SIZE`：存储空间限制提示信息
- `-g, --gpu-memory SIZE`：GPU显存限制（例如：1g, 2048m）
- `-t, --timeout SECONDS`：运行时长限制（秒，默认：3600）
- `--streamable-http`：启用Streamable HTTP模式（默认：false）
- `--notebook`：启用Jupyter Notebook服务（默认：false）
- `--external-host HOST`：指定外部访问主机域名/IP（默认：localhost），用于提供下载链接
- `--include-port`：下载链接中，ip后面是否包含70端口，一般域名填false，ip填true
### API接口

#### 1. 执行Python代码

```bash
curl -X POST http://localhost:7000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, World!\")"}'
```

#### 2. 安装Python包

```bash
curl -X POST http://localhost:7000/install \
  -H "Content-Type: application/json" \
  -d '{"package": "numpy"}'
```

## Streamable HTTP URL集成

该MCP服务支持通过Streamable HTTP URL与大模型集成。您可以使用以下方式与服务交互：

### 启动支持Streamable HTTP的容器

```bash
# 启动支持Streamable HTTP的容器
./start_mcp_container.sh -c 2 -m 2g -t 3600

# 或者在已有容器中直接运行Streamable HTTP服务
docker run -d --name mcp-streamable -p 7000:7000 python-mcp-server-notebook:latest python /app/mcp_server.py streamable
```

### Streamable HTTP MCP协议使用方法

Streamable HTTP MCP服务遵循JSON-RPC 2.0协议，支持Server-Sent Events (SSE)传输。

#### 1. 初始化会话

```bash
# 初始化MCP会话
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {"tools": {}},
      "clientInfo": {"name": "your-client", "version": "1.0.0"}
    }
  }'
```

从响应头中获取`Mcp-Session-Id`，后续请求需要包含此ID。

#### 2. 获取工具列表

```bash
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'
```

#### 3. 执行Python代码

```bash
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "execute_code_tool",
      "arguments": {
        "code": "print(\"Hello from Streamable HTTP MCP!\")"
      }
    }
  }'
```

#### 4. 安装Python包

```bash
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "install_package_tool",
      "arguments": {
        "package": "requests"
      }
    }
  }'
```

### Python客户端示例

```python
import requests
import json

class StreamableMCPClient:
    def __init__(self, endpoint="http://localhost:7000/mcp"):
        self.endpoint = endpoint
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    
    def initialize(self):
        """初始化MCP会话"""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "python-client", "version": "1.0.0"}
            }
        }
        
        response = requests.post(self.endpoint, json=init_request, headers=self.headers)
        self.session_id = response.headers.get('Mcp-Session-Id')
        if self.session_id:
            self.headers["Mcp-Session-Id"] = self.session_id
        return response
    
    def call_tool(self, tool_name, arguments):
        """调用MCP工具"""
        tool_request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(self.endpoint, json=tool_request, headers=self.headers)
        return response
    
    def execute_code(self, code):
        """执行Python代码"""
        return self.call_tool("execute_code_tool", {"code": code})
    
    def install_package(self, package):
        """安装Python包"""
        return self.call_tool("install_package_tool", {"package": package})
    
    def _get_next_id(self):
        """生成请求ID"""
        if not hasattr(self, '_id_counter'):
            self._id_counter = 1
        else:
            self._id_counter += 1
        return self._id_counter

# 使用示例
client = StreamableMCPClient()
client.initialize()

# 执行代码
result = client.execute_code("print('Hello from Python client!')")
print("执行结果:", result.text)

# 安装包
result = client.install_package("requests")
print("安装结果:", result.text)
```

### 可用工具说明

MCP服务提供以下内置工具：

1. **execute_code_tool**: 执行Python代码
   - 参数: `code` (string) - 要执行的Python代码

2. **install_package_tool**: 安装Python包
   - 参数: `package` (string) - 要安装的包名

3. **health_check_tool**: 检查服务健康状态
   - 参数: 无

### 传统API接口（保持兼容）

### 大模型集成示例

```python
import requests
import json

# MCP服务地址
MCP_ENDPOINT = "http://localhost:7000"

def execute_python_code(code):
    """执行Python代码"""
    response = requests.post(
        f"{MCP_ENDPOINT}/execute",
        headers={"Content-Type": "application/json"},
        json={"code": code}
    )
    return response.json()

def install_packages(packages):
    """安装Python包"""
    response = requests.post(
        f"{MCP_ENDPOINT}/install",
        headers={"Content-Type": "application/json"},
        json={"package": packages}
    )
    return response.json()

# 示例：安装数据分析包并执行代码
install_packages("pandas numpy")
result = execute_python_code("""
import pandas as pd
import numpy as np

# 创建示例数据
data = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100)
})

# 执行分析
correlation = data.corr()
print(f"相关系数矩阵:\n{correlation}")
""")
print(result)
```

## 示例

### 执行简单代码

```bash
curl -X POST http://localhost:7000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Current working directory:\", __import__(\"os\").getcwd())"}'
```

### 安装并使用包

```bash
# 安装包
curl -X POST http://localhost:7000/install \
  -H "Content-Type: application/json" \
  -d '{"package": "requests"}'

# 使用已安装的包
curl -X POST http://localhost:7000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "import requests\nprint(\"Requests version:\", requests.__version__)"}'
```

## GPU支持

本系统支持GPU加速，需要满足以下条件：

1. 宿主机安装了NVIDIA驱动
2. 安装了NVIDIA Container Toolkit
3. 有可用的NVIDIA GPU

### 启用GPU支持

```bash
# 启动带GPU支持的容器
./start_mcp_container.sh -g 2g  # 限制GPU显存为2GB

# 启动带GPU和CPU/内存限制的容器
./start_mcp_container.sh -c 2 -m 4g -g 2g
```

### 在代码中使用GPU

```bash
# 安装GPU支持的包
curl -X POST http://localhost:7000/install \
  -H "Content-Type: application/json" \
  -d '{"package": "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"}'

# 执行GPU代码
curl -X POST http://localhost:7000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "import torch\nprint(f\"CUDA可用: {torch.cuda.is_available()}\")\nprint(f\"GPU数量: {torch.cuda.device_count()}\")"}'
```

## 安全说明

1. 每个容器实例运行在隔离环境中
2. 有资源限制防止滥用
3. 容器超时自动停止
4. 工作区文件与宿主机隔离

## 注意事项

1. 确保Docker服务正在运行
2. 首次使用前需要构建Docker镜像
3. 容器默认绑定到7000端口，请确保端口未被占用
4. 工作区文件保存在宿主机对应目录中，容器停止后仍然存在