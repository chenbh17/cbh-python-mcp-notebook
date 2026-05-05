# 文件上传下载使用指南

## 概述

MCP 服务器的文件上传/下载功能通过**HTTP API**实现，客户端可以直接与容器进行文件传输。

## 架构说明

```
┌─────────────┐      HTTP POST       ┌──────────────┐
│   客户端     │ ───────────────────► │  容器 (7000)  │
│  (本地电脑)  │                      │  /upload     │
│             │ ◄─────────────────── │              │
│             │      返回 upload_url   │              │
└─────────────┘                      └──────────────┘
       │
       │ HTTP GET/POST
       ▼
┌──────────────┐
│  容器 (777)   │
│  /download   │
└──────────────┘
```

**关键点**：
- 所有 URL 通过 Nginx 统一代理（端口 70）
- URL 格式：`http://{external-host}:70/{container_id}/{upload|download}`
- `external-host`和是否包含端口由启动参数决定

## 启动参数说明

启动容器时使用的参数会影响 URL 格式：

```bash
./start_mcp_container.sh \
  --external-host chenbh17-python-mcp.iepose.cn \
  --include-port false \
  -c 2 -m 4g
```

**URL 构建规则**：

| external-host | include-port | URL 格式 |
|--------------|-------------|---------|
| 域名 (chenbh17-python-mcp.iepose.cn) | false | `http://chenbh17-python-mcp.iepose.cn/{container_id}/...` |
| 域名 | true | `http://chenbh17-python-mcp.iepose.cn:70/{container_id}/...` |
| IP (115.190.211.94) | false | `http://115.190.211.94/{container_id}/...` |
| IP | true | `http://115.190.211.94:70/{container_id}/...` |

**默认行为**：
- 域名：默认 `include-port=false`
- IP 地址：默认 `include-port=true`

---

## 文件上传

### 步骤 1：调用 MCP 工具获取上传 URL

```python
from mcp import Client

client = Client("http://localhost:7000/mcp")

# 调用工具获取上传 URL
result = client.call_tool('upload_file', {
    'container_file_path': 'data/train.csv'
})

print(result)
# 输出示例：
# {
#   "success": True,
#   "upload_url": "http://chenbh17-python-mcp.iepose.cn/557de3c49b56/upload",
#   "container_file_path": "data/train.csv",
#   "container_id": "557de3c49b56"
# }

upload_url = result['upload_url']
```

### 步骤 2：通过 HTTP POST 上传文件

#### 方法 1：使用 Python requests 库（推荐）

```python
import requests

# 上传文件
with open('local_file.csv', 'rb') as f:
    files = {'file': f}
    data = {'filepath': 'data/train.csv'}
    response = requests.post(upload_url, files=files, data=data)

print(response.json())
# 输出：
# {
#   "success": True,
#   "message": "文件上传成功",
#   "target_path": "/workspace/data/train.csv",
#   "file_size": 1024000
# }
```

#### 方法 2：使用 curl 命令

```bash
curl -X POST http://chenbh17-python-mcp.iepose.cn/557de3c49b56/upload \
  -F "file=@local_file.csv" \
  -F "filepath=data/train.csv"
```

#### 方法 3：从 HTTP URL 自动下载

如果文件已经在某个 HTTP 服务器上，可以让容器自动下载：

```python
import requests

response = requests.post(upload_url, json={
    'filepath': 'data/train.csv',
    'file_url': 'https://example.com/data.csv'
})
```

---

## 文件下载

### 步骤 1：调用 MCP 工具获取下载 URL

```python
from mcp import Client

client = Client("http://localhost:7000/mcp")

# 调用工具获取下载 URL
result = client.call_tool('download_file', {
    'container_file_path': 'output/result.csv'
})

print(result)
# 输出示例：
# {
#   "success": True,
#   "download_url": "http://chenbh17-python-mcp.iepose.cn/557de3c49b56/download/output/result.csv",
#   "file_exists": True,
#   "file_size": "2048000 bytes",
#   "filename": "result.csv"
# }

download_url = result['download_url']
```

### 步骤 2：通过 HTTP GET 下载文件

#### 方法 1：使用 Python requests 库（推荐）

```python
import requests

# 下载文件
response = requests.get(download_url)

# 保存到本地
with open('local_result.csv', 'wb') as f:
    f.write(response.content)

print(f"文件已保存到 local_result.csv")
```

#### 方法 2：使用 wget 命令

```bash
wget http://chenbh17-python-mcp.iepose.cn/557de3c49b56/download/output/result.csv \
  -O local_result.csv
```

#### 方法 3：直接在浏览器打开

将 `download_url` 在浏览器中打开即可下载文件。

---

## 完整示例

### 示例 1：上传 CSV 文件进行分析

```python
import requests
from mcp import Client

# 初始化 MCP 客户端
client = Client("http://localhost:7000/mcp")

# 1. 获取上传 URL
upload_result = client.call_tool('upload_file', {
    'container_file_path': 'data/my_data.csv'
})
upload_url = upload_result['upload_url']

# 2. 上传文件
with open('my_data.csv', 'rb') as f:
    files = {'file': f}
    data = {'filepath': 'data/my_data.csv'}
    response = requests.post(upload_url, files=files, data=data)

# 3. 执行分析
client.call_tool('descriptive_statistics', {
    'data_file_path': '/workspace/data/my_data.csv',
    'output_dir': 'desc_stats'
})

# 4. 获取结果下载 URL
download_result = client.call_tool('download_file', {
    'container_file_path': 'desc_stats/desc_num_rpt.xlsx'
})
download_url = download_result['download_url']

# 5. 下载报告
response = requests.get(download_url)
with open('analysis_report.xlsx', 'wb') as f:
    f.write(response.content)

print("分析完成！报告已保存。")
```

### 示例 2：上传模型文件进行预测

```python
import requests
import base64

# 1. 上传模型文件（二进制文件）
upload_result = client.call_tool('upload_file', {
    'container_file_path': 'models/my_model.pkl'
})
upload_url = upload_result['upload_url']

# 读取模型文件并上传
with open('my_model.pkl', 'rb') as f:
    files = {'file': ('my_model.pkl', f, 'application/octet-stream')}
    data = {'filepath': 'models/my_model.pkl'}
    response = requests.post(upload_url, files=files, data=data)

# 2. 上传测试数据
upload_result = client.call_tool('upload_file', {
    'container_file_path': 'data/test_data.csv'
})
upload_url = upload_result['upload_url']

with open('test_data.csv', 'rb') as f:
    files = {'file': f}
    data = {'filepath': 'data/test_data.csv'}
    response = requests.post(upload_url, files=files, data=data)

print("模型和数据已上传，可以在容器中进行预测。")
```

---

## 注意事项

### 文件大小限制

- 建议单个文件不超过 **100MB**
- 超大文件建议：
  - 使用 URL 方式（容器自动从 HTTP 服务器下载）
  - 分块上传

### 路径规范

- 容器内路径都相对于 `/workspace` 目录
- 不要使用绝对路径或 `..` 上级目录
- 示例：`data/train.csv` ✅，`/workspace/data/train.csv` ❌

### 安全提示

- 确保容器正在运行
- 下载 URL 有效期与容器运行时间相同
- 容器停止后，URL 失效

### 常见问题

**Q: 上传/下载失败怎么办？**

A: 检查以下几点：
1. 容器是否正在运行：`docker ps | grep python-mcp-container`
2. URL 是否正确（特别是 container_id）
3. 网络是否可达
4. 文件路径是否正确

**Q: 如何获取 container_id？**

A: 有三种方式：
1. 调用 `upload_file` 或 `download_file` 工具，返回结果中包含 `container_id`
2. 查看容器列表：`docker ps --filter "name=python-mcp-container"`
3. 从 Gradio 管理界面查看：`http://localhost:7070`

**Q: 支持哪些文件类型？**

A: 支持所有文件类型：
- 文本文件：CSV、TXT、JSON、XML 等
- 二进制文件：Excel、图片、模型文件、压缩包等

---

## API 参考

### 上传 API

**端点**: `POST /{container_id}/upload`

**请求格式 1** (multipart/form-data):
```
Content-Type: multipart/form-data

file: <文件内容>
filepath: data/train.csv
```

**请求格式 2** (JSON):
```json
{
  "filepath": "data/train.csv",
  "file_url": "https://example.com/data.csv"
}
```

**响应**:
```json
{
  "success": true,
  "message": "文件上传成功",
  "target_path": "/workspace/data/train.csv",
  "file_size": 1024000
}
```

### 下载 API

**端点**: `GET /{container_id}/download/{filepath}`

**响应**: 文件内容（二进制流）

---

## 更新日志

- **2026-04-02**: 修改为通过 HTTP API 传输，支持任意客户端文件上传下载
- 旧版本问题：只能在容器内部复制文件，无法与客户端通信
