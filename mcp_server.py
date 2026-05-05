import os
import sys
import subprocess
import json
import tempfile
import time
import threading
import shutil
from flask import Flask, request, jsonify, send_file, send_from_directory
import requests
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

app = Flask(__name__)

# 工作目录
WORKSPACE_DIR = "/workspace"

# 创建FastMCP实例
mcp = FastMCP("python-mcp-server")
# 禁用 DNS rebinding 保护，允许任意 Host header
mcp.settings.transport_security.enable_dns_rebinding_protection = False


# 导入 cbhpacks MCP 工具
try:
    from cbhpacks_mcp_tools import (
        # 数据生成
        generate_random_data,
        # 分箱分析
        create_bins_report,
        transform_to_woe,
        get_psi_report,
        # 特征选择
        feature_selection,
        bootstrap_feature_selection,
        recursive_feature_selection,
        # 特征编码
        encode_features,
        # 模型训练
        train_binary_model,
        generate_model_report,
        # 无监督学习
        pca_analysis,
        kmeans_clustering,
        # 回归分析
        linear_regression,
        # 描述统计
        descriptive_statistics,
        single_column_analysis,
        # 特征工程
        rfms_feature_engineering,
        create_hive_table,
        # 数据库查询
        query_clickhouse,
        execute_clickhouse,
        query_mysql,
        query_hive,
        save_to_hive,
        # Linux 命令
        execute_linux_command,
        # 文件传输
        upload_file,
        download_file
    )
    
    # 注册 cbhpacks 工具到 MCP（cbhpacks 特有工具）
    mcp.tool()(generate_random_data)
    mcp.tool()(create_bins_report)
    mcp.tool()(transform_to_woe)
    mcp.tool()(get_psi_report)
    mcp.tool()(feature_selection)
    mcp.tool()(bootstrap_feature_selection)
    mcp.tool()(recursive_feature_selection)
    mcp.tool()(encode_features)
    mcp.tool()(train_binary_model)
    mcp.tool()(generate_model_report)
    mcp.tool()(pca_analysis)
    mcp.tool()(kmeans_clustering)
    mcp.tool()(linear_regression)
    mcp.tool()(descriptive_statistics)
    mcp.tool()(single_column_analysis)
    mcp.tool()(rfms_feature_engineering)
    mcp.tool()(create_hive_table)
    mcp.tool()(query_clickhouse)
    mcp.tool()(execute_clickhouse)
    mcp.tool()(query_mysql)
    mcp.tool()(query_hive)
    mcp.tool()(save_to_hive)
    mcp.tool()(execute_linux_command)
    mcp.tool()(upload_file)
    mcp.tool()(download_file)
    
    print("cbhpacks MCP tools registered successfully!")
except ImportError as e:
    print(f"Warning: Could not import cbhpacks_mcp_tools: {e}")

# 文件下载Flask应用
download_app = Flask(__name__)

class MCPAdapter:
    """MCP适配器，用于在Streamable HTTP中执行代码和安装包"""
    
    @staticmethod
    def install_package(package_name):
        """安装Python包"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package_name
            ], capture_output=True, text=True, cwd=WORKSPACE_DIR)
            
            if result.returncode == 0:
                return {"success": True, "message": f"Package '{package_name}' installed successfully"}
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def execute_code(code):
        """执行Python代码"""
        try:
            # 创建临时文件执行代码
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=WORKSPACE_DIR, delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # 执行代码
            result = subprocess.run([
                sys.executable, temp_file
            ], capture_output=True, text=True, cwd=WORKSPACE_DIR, timeout=7200)
            
            # 清理临时文件
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Code execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def execute_terminal_command(command):
        """执行终端命令"""
        try:
            # 执行终端命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=WORKSPACE_DIR,
                timeout=7200
            )
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def list_files(path=""):
        """列出目录中的文件"""
        try:
            full_path = os.path.join(WORKSPACE_DIR, path) if path else WORKSPACE_DIR
            if os.path.exists(full_path) and os.path.isdir(full_path):
                files = os.listdir(full_path)
                file_info = []
                for file in files:
                    file_path = os.path.join(full_path, file)
                    stat_info = os.stat(file_path)
                    file_info.append({
                        "name": file,
                        "is_dir": os.path.isdir(file_path),
                        "size": stat_info.st_size,
                        "modified": time.ctime(stat_info.st_mtime)
                    })
                return {"success": True, "files": file_info}
            else:
                return {"success": False, "error": "Path not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# 添加MCP工具
@mcp.tool()
def install_package_tool(package: str) -> dict:
    """安装Python包的MCP工具"""
    return MCPAdapter.install_package(package)

@mcp.tool()
def execute_code_tool(code: str) -> dict:
    """执行Python代码的MCP工具"""
    return MCPAdapter.execute_code(code)

@mcp.tool()
def health_check_tool() -> dict:
    """健康检查的MCP工具"""
    return {"status": "healthy"}

@mcp.tool()
def execute_terminal_command_tool(command: str) -> dict:
    """执行终端命令的MCP工具"""
    return MCPAdapter.execute_terminal_command(command)

@mcp.tool()
def list_files_tool(path: str = "") -> dict:
    """列出文件的MCP工具"""
    return MCPAdapter.list_files(path)

@mcp.tool()
def get_download_link_tool(filepath: str) -> dict:
    """获取文件下载链接的MCP工具"""
    try:
        import os
        import socket
        # 优先使用hostname作为容器ID（这是Docker容器的短ID）
        hostname = socket.gethostname()
        # 检查hostname是否是有效的Docker容器短ID（12个十六进制字符）
        if len(hostname) == 12 and all(c in '0123456789abcdef' for c in hostname.lower()):
            container_id = hostname
        else:
            # 如果hostname不是有效的短ID，回退到环境变量
            container_id = os.environ.get('CONTAINER_ID', hostname)
        
        # 确保filepath是相对路径，移除前导的/workspace/或/
        if filepath.startswith('/workspace/'):
            filepath = filepath[len('/workspace/'):]
        elif filepath.startswith('/'):
            filepath = filepath[1:]
            
        # 获取外部主机名和端口配置
        external_host = os.environ.get('EXTERNAL_HOST', 'localhost')
        include_port = os.environ.get('INCLUDE_PORT', 'true').lower() == 'true'
        
        # 判断是否为IP地址格式
        import re
        is_ip_address = re.match(r'^\d+\.\d+\.\d+\.\d+$', external_host) is not None
        
        # 对于域名，默认不包含端口；对于IP地址，默认包含端口
        if is_ip_address:
            include_port = os.environ.get('INCLUDE_PORT', 'true').lower() == 'true'
        else:
            include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
        
        # 构建下载URL
        if include_port:
            download_url = f"http://{external_host}:70/{container_id}/download/{filepath}"
        else:
            download_url = f"http://{external_host}/{container_id}/download/{filepath}"
            
        return {"success": True, "download_url": download_url}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/install', methods=['POST'])
def install():
    """安装依赖包的API端点"""
    data = request.json
    package_name = data.get('package')
    
    if not package_name:
        return jsonify({"success": False, "error": "Package name is required"}), 400
    
    result = MCPAdapter.install_package(package_name)
    return jsonify(result)

@app.route('/execute', methods=['POST'])
def execute():
    """执行代码的API端点"""
    data = request.json
    code = data.get('code')
    
    if not code:
        return jsonify({"success": False, "error": "Code is required"}), 400
    
    result = MCPAdapter.execute_code(code)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """健康检查端点"""
    return jsonify({"status": "healthy"})

# 文件上传端点
@app.route('/upload', methods=['POST'])
def upload_file_api():
    """上传文件到容器"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            # 尝试从 JSON body 获取 base64 内容
            data = request.json
            if data and 'content' in data and 'filepath' in data:
                import base64
                content = data['content']
                filepath = data['filepath']
                encoding = data.get('encoding', 'utf-8')
                
                target_path = os.path.join(WORKSPACE_DIR, filepath.lstrip('/'))
                target_dir = os.path.dirname(target_path)
                os.makedirs(target_dir, exist_ok=True)
                
                if encoding == 'base64':
                    with open(target_path, 'wb') as f:
                        f.write(base64.b64decode(content))
                else:
                    with open(target_path, 'w', encoding=encoding) as f:
                        f.write(content)
                
                return jsonify({
                    "success": True,
                    "message": "文件上传成功",
                    "target_path": target_path,
                    "file_size": os.path.getsize(target_path)
                })
            return jsonify({"success": False, "error": "No file or content provided"}), 400
        
        file = request.files['file']
        filepath = request.form.get('filepath', file.filename)
        
        if not filepath:
            return jsonify({"success": False, "error": "No filepath provided"}), 400
        
        # 确保路径安全
        safe_path = os.path.normpath(filepath)
        if safe_path.startswith("/"):
            safe_path = safe_path[1:]
        if safe_path.startswith(".."):
            return jsonify({"success": False, "error": "Invalid file path"}), 400
        
        target_path = os.path.join(WORKSPACE_DIR, safe_path)
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # 保存文件
        file.save(target_path)
        
        return jsonify({
            "success": True,
            "message": "文件上传成功",
            "target_path": target_path,
            "file_size": os.path.getsize(target_path)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def build_container_url(container_id, path_type, filepath):
    """
    构建容器访问 URL
    
    Args:
        container_id: 容器 ID（短 ID）
        path_type: 路径类型 ('upload' 或 'download')
        filepath: 文件路径
    
    Returns:
        完整的 URL
    """
    # 获取外部主机名和端口配置
    external_host = os.environ.get('EXTERNAL_HOST', 'localhost')
    include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
    
    # 判断是否为 IP 地址格式
    import re
    is_ip_address = re.match(r'^\d+\.\d+\.\d+\.\d+$', external_host) is not None
    
    # 对于域名，默认不包含端口；对于 IP 地址，默认包含端口
    if is_ip_address:
        include_port = os.environ.get('INCLUDE_PORT', 'true').lower() == 'true'
    else:
        include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
    
    # 构建基础 URL
    if include_port:
        base_url = f"http://{external_host}:70"
    else:
        base_url = f"http://{external_host}"
    
    # 构建完整 URL
    if path_type == 'upload':
        return f"{base_url}/{container_id}/upload"
    elif path_type == 'download':
        return f"{base_url}/{container_id}/download/{filepath.lstrip('/')}"
    else:
        return f"{base_url}/{container_id}/"


# 文件下载端点
@download_app.route('/download/<path:filename>')
def download_file(filename):
    """下载文件"""
    try:
        # 确保文件路径在工作目录内
        safe_path = os.path.normpath(filename)
        # 移除前导斜杠（如果有）
        if safe_path.startswith("/"):
            safe_path = safe_path[1:]
        # 检查路径是否安全
        if safe_path.startswith(".."):
            return jsonify({"success": False, "error": "Invalid file path"}), 400
        
        file_path = os.path.join(WORKSPACE_DIR, safe_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 文件上传端点 (在 download_app 上也注册，用于接收外部上传)
@download_app.route('/upload', methods=['POST'])
def upload_file_download_app():
    """上传文件到容器（download_app 版本）"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        filepath = request.form.get('filepath', file.filename)
        
        if not filepath:
            return jsonify({"success": False, "error": "No filepath provided"}), 400
        
        # 确保路径安全
        safe_path = os.path.normpath(filepath)
        if safe_path.startswith("/"):
            safe_path = safe_path[1:]
        if safe_path.startswith(".."):
            return jsonify({"success": False, "error": "Invalid file path"}), 400
        
        target_path = os.path.join(WORKSPACE_DIR, safe_path)
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # 保存文件
        file.save(target_path)
        
        return jsonify({
            "success": True,
            "message": "文件上传成功",
            "target_path": target_path,
            "file_size": os.path.getsize(target_path)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 终端命令执行端点
@app.route('/terminal', methods=['POST'])
def terminal():
    """执行终端命令"""
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({"success": False, "error": "Command is required"}), 400
    
    result = MCPAdapter.execute_terminal_command(command)
    return jsonify(result)

# 文件列表端点
@app.route('/files', methods=['GET'])
def list_files():
    """列出文件"""
    path = request.args.get('path', '')
    result = MCPAdapter.list_files(path)
    return jsonify(result)

# 创建Streamable HTTP应用并添加中间件
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# 直接使用MCP的streamable_http_app并添加中间件
# 禁用 DNS rebinding 保护，允许任意 Host header
mcp.settings.transport_security.enable_dns_rebinding_protection = False
streamable_app = mcp.streamable_http_app()


# 添加CORS中间件
streamable_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    expose_headers=["Mcp-Session-Id"],
)

if __name__ == '__main__':
    import asyncio
    import sys
    
    # 检查命令行参数来决定运行模式
    if len(sys.argv) > 1 and sys.argv[1] == 'streamable':
        # 运行Streamable HTTP服务
        print("Starting Streamable HTTP MCP server on port 7000...")
        uvicorn.run("mcp_server:streamable_app", host="0.0.0.0", port=7000, log_level="info")
    else:
        # 运行原有的Flask服务
        print("Starting Flask API server on port 7000...")
        # 启动主Flask服务
        from threading import Thread
        
        def start_main_server():
            app.run(host='0.0.0.0', port=7000)
        
        def start_download_server():
            # 查找可用端口（从777开始）
            download_port = 777
            import socket
            while True:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(('localhost', download_port)) != 0:
                        break
                download_port += 1
            
            # 设置环境变量供下载链接使用
            os.environ['DOWNLOAD_PORT'] = str(download_port)
            download_app.run(host='0.0.0.0', port=download_port)
        
        # 启动两个服务
        main_thread = Thread(target=start_main_server)
        download_thread = Thread(target=start_download_server)
        
        main_thread.start()
        download_thread.start()
        
        main_thread.join()
        download_thread.join()