#!/usr/bin/env python3
"""
Python容器管理前端界面
使用Gradio创建一个Web界面来管理MCP容器
"""

import gradio as gr
import docker
import subprocess
import json
import time
import os
from datetime import datetime, timedelta

# 初始化Docker客户端
client = docker.from_env()

def get_container_info(container):
    """获取容器详细信息"""
    try:
        # 获取容器详细信息
        info = client.api.inspect_container(container.id)
        
        # 基本信息
        container_id = container.short_id
        name = container.name
        status = container.status
        created = info['Created']
        
        # 解析创建时间
        created_time = datetime.strptime(created.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        uptime = datetime.utcnow() - created_time.replace(tzinfo=None)
        
        # 端口信息
        ports = info['NetworkSettings']['Ports']
        mcp_port = None
        notebook_port = None
        
        if '7000/tcp' in ports and ports['7000/tcp']:
            mcp_port = ports['7000/tcp'][0]['HostPort']
        
        if '7777/tcp' in ports and ports['7777/tcp']:
            notebook_port = ports['7777/tcp'][0]['HostPort']
        
        # 资源限制
        host_config = info['HostConfig']
        cpu_cores = host_config.get('NanoCpus', 0) / 1000000000 if host_config.get('NanoCpus') else host_config.get('CpuCount', 0)
        memory_limit = host_config.get('Memory', 0)
        gpu_support = 'Yes' if host_config.get('DeviceRequests') else 'No'
        
        # 挂载目录
        mounts = info['Mounts']
        workspace_dir = ""
        for mount in mounts:
            if mount['Destination'] == '/workspace':
                workspace_dir = mount['Source']
                break
        
        # 计算剩余时间（基于启动脚本的超时机制）
        # 从容器环境变量中获取超时设置
        timeout_seconds = 3600  # 默认1小时
        env_vars = info.get('Config', {}).get('Env', [])
        for env_var in env_vars:
            if env_var.startswith('CONTAINER_TIMEOUT='):
                try:
                    timeout_seconds = int(env_var.split('=')[1])
                    break
                except:
                    pass
        
        # 计算已运行时间（秒）
        uptime_seconds = uptime.total_seconds()
        
        # 计算剩余时间
        remaining_seconds = max(0, timeout_seconds - uptime_seconds)
        if remaining_seconds > 0:
            remaining_time = str(timedelta(seconds=int(remaining_seconds)))
        else:
            remaining_time = "Expired"
        
        return {
            'id': container_id,
            'name': name,
            'status': status,
            'created': created_time.strftime("%Y-%m-%d %H:%M:%S"),
            'uptime': str(uptime).split('.')[0],  # 移除微秒部分
            'remaining': remaining_time,
            'mcp_port': mcp_port,
            'notebook_port': notebook_port,
            'cpu_cores': cpu_cores,
            'memory_limit': f"{memory_limit / (1024**3):.1f} GB" if memory_limit > 0 else "Unlimited",
            'gpu_support': gpu_support,
            'workspace_dir': workspace_dir,
            'mcp_url': f"https://chenbh17-python-mcp.iepose.cn/{container_id}/mcp" if mcp_port else "N/A",
            'notebook_url': f"https://chenbh17-python-mcp.iepose.cn/{container_id}/notebook" if notebook_port else "N/A"
        }
    except Exception as e:
        return {
            'id': container.short_id,
            'name': container.name,
            'status': f"Error: {str(e)}",
            'created': "N/A",
            'uptime': "N/A",
            'remaining': "N/A",
            'mcp_port': "N/A",
            'notebook_port': "N/A",
            'cpu_cores': "N/A",
            'memory_limit': "N/A",
            'gpu_support': "N/A",
            'workspace_dir': "N/A",
            'mcp_url': "N/A",
            'notebook_url': "N/A"
        }

def list_containers():
    """列出所有MCP容器"""
    try:
        # 获取所有容器（包括停止的）
        all_containers = client.containers.list(all=True)
        
        # 筛选出MCP容器
        mcp_containers = [c for c in all_containers if c.name.startswith('python-mcp-container')]
        
        # 获取容器详细信息
        container_details = []
        for container in mcp_containers:
            details = get_container_info(container)
            container_details.append(details)
        
        return container_details
    except Exception as e:
        return [{"error": f"Failed to list containers: {str(e)}"}]

def format_container_table(containers):
    """格式化容器信息为表格"""
    if not containers:
        return "<p>No containers found</p>", ""
    
    # 表头
    table = """
    <style>
    .container-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        user-select: text;
    }
    .container-table th, .container-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .container-table th {
        background-color: #f2f2f2;
        position: sticky;
        top: 0;
    }
    .container-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .container-table tr:hover {
        background-color: #f5f5f5;
    }
    .container-id {
        user-select: text;
        cursor: text;
        font-family: monospace;
    }
    </style>
    <table class="container-table">
    <thead>
    <tr>
        <th>运行中的容器ID</th>
        <th>名称</th>
        <th>状态</th>
        <th>创建时间</th>
        <th>已运行时间</th>
        <th>剩余时间</th>
        <th>MCP端口</th>
        <th>Notebook端口</th>
        <th>CPU核心</th>
        <th>内存限制</th>
        <th>GPU支持</th>
    </tr>
    </thead>
    <tbody>
    """
    
    # 表格内容
    for container in containers:
        if 'error' in container:
            return f"<p>Error: {container['error']}</p>", ""
            
        container_id = container['id']
        table += f"""
        <tr>
            <td class="container-id">{container_id}</td>
            <td>{container['name']}</td>
            <td>{container['status']}</td>
            <td>{container['created']}</td>
            <td>{container['uptime']}</td>
            <td>{container['remaining']}</td>
            <td>{container['mcp_port'] or 'N/A'}</td>
            <td>{container['notebook_port'] or 'N/A'}</td>
            <td>{container['cpu_cores']}</td>
            <td>{container['memory_limit']}</td>
            <td>{container['gpu_support']}</td>
        </tr>
        """
    
    table += """
    </tbody>
    </table>
    """
    
    return table, ""

def format_container_details(containers):
    """格式化容器详细信息"""
    if not containers:
        return "No containers found"
    
    details = ""
    for container in containers:
        if 'error' in container:
            return container['error']
            
        details += f"""
## 容器详细信息: {container['name']}

- **容器ID**: {container['id']}
- **状态**: {container['status']}
- **创建时间**: {container['created']}
- **已运行时间**: {container['uptime']}
- **剩余时间**: {container['remaining']}
- **MCP端口**: {container['mcp_port'] or 'N/A'}
- **Notebook端口**: {container['notebook_port'] or 'N/A'}
- **CPU核心**: {container['cpu_cores']}
- **内存限制**: {container['memory_limit']}
- **GPU支持**: {container['gpu_support']}
- **工作目录**: {container['workspace_dir']}

### 访问地址

- **MCP访问地址**: [{container['mcp_url']}]({container['mcp_url']})
- **Notebook访问地址**: [{container['notebook_url']}]({container['notebook_url']})

---
"""
    
    return details

def start_container(cpu_cores, memory, gpu_memory, timeout, streamable_http, enable_notebook, external_host, include_port):
    """启动新的容器"""
    try:
        # 构建启动命令
        cmd = ["./start_mcp_container.sh"]
        
        # 添加参数
        if cpu_cores:
            cmd.extend(["-c", str(cpu_cores)])
        if memory:
            cmd.extend(["-m", memory])
        if gpu_memory:
            cmd.extend(["-g", gpu_memory])
        if timeout:
            cmd.extend(["-t", str(timeout)])
        if streamable_http:
            cmd.append("--streamable-http")
        if enable_notebook:
            cmd.append("--notebook")
        if external_host:
            cmd.extend(["--external-host", external_host])
        if include_port and include_port != "auto":
            cmd.extend(["--include-port", include_port])
        
        # 异步执行启动命令，不等待结果
        subprocess.Popen(cmd, cwd=".")
        
        # 直接返回提示信息，而不是等待执行结果
        return "已发送启动请求，请在容器列表刷新查看启动结果"
    except Exception as e:
        return f"启动容器时发生错误: {str(e)}"

def stop_container(container_name):
    """停止指定容器"""
    try:
        if not container_name:
            return "请选择要停止的容器"
            
        # 停止容器
        result = subprocess.run(["docker", "stop", container_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"容器 {container_name} 已成功停止"
        else:
            return f"停止容器失败: {result.stderr}"
    except Exception as e:
        return f"停止容器时发生错误: {str(e)}"

def refresh_containers():
    """刷新容器列表"""
    containers = list_containers()
    table_html, _ = format_container_table(containers)
    details = format_container_details(containers)
    return table_html, details

# 创建Gradio界面
with gr.Blocks(title="Python MCP容器管理器") as demo:
    gr.Markdown("# Python MCP容器管理器")
    gr.Markdown("管理Python MCP容器的Web界面，可以启动、停止和监控容器")
    
    # 添加自定义CSS样式以支持更好的复制体验
    demo.load(None, None, None, js="""
    () => {
        const style = document.createElement('style');
        style.textContent = `
            .container-table td:first-child {
                user-select: text !important;
                -webkit-user-select: text !important;
                cursor: text !important;
            }
            .container-table {
                user-select: text !important;
            }
        `;
        document.head.appendChild(style);
    }
    """)
    
    with gr.Tab("容器列表"):
        with gr.Row():
            refresh_btn = gr.Button("刷新容器列表")
        
        with gr.Row():
            container_table = gr.HTML(label="容器列表")
        
        # 添加容器详情查询部分
        with gr.Row():
            container_id_input = gr.Textbox(label="输入容器ID查询详情", placeholder="请输入容器ID")
            get_details_btn = gr.Button("获取容器详情")
        
        container_details = gr.Markdown(label="容器详细信息")
        
        refresh_btn.click(
            refresh_containers,
            outputs=[container_table, container_details]
        )
        
        # 容器详情查询功能
        def get_container_details_by_id(container_id):
            """根据容器ID获取详细信息"""
            if not container_id:
                return "请输入容器ID"
            
            containers = list_containers()
            for container in containers:
                if container.get('id') == container_id:
                    # 只显示特定容器的详细信息
                    details = f"""
## 容器详细信息: {container['name']}

- **容器ID**: {container['id']}
- **状态**: {container['status']}
- **创建时间**: {container['created']}
- **已运行时间**: {container['uptime']}
- **剩余时间**: {container['remaining']}
- **MCP端口**: {container['mcp_port'] or 'N/A'}
- **Notebook端口**: {container['notebook_port'] or 'N/A'}
- **CPU核心**: {container['cpu_cores']}
- **内存限制**: {container['memory_limit']}
- **GPU支持**: {container['gpu_support']}
- **工作目录**: {container['workspace_dir']}

### 访问地址

- **MCP访问地址**: [{container['mcp_url']}]({container['mcp_url']})
- **Notebook访问地址**: [{container['notebook_url']}]({container['notebook_url']})
"""
                    return details
            
            return f"未找到ID为 {container_id} 的容器"
        
        get_details_btn.click(
            get_container_details_by_id,
            inputs=container_id_input,
            outputs=container_details
        )
    
    with gr.Tab("启动容器"):
        gr.Markdown("## 启动新的容器")
        
        with gr.Row():
            cpu_cores = gr.Number(label="CPU核心数", value=1, minimum=1, maximum=512, step=1)
            memory = gr.Textbox(label="内存限制 (如: 1g, 2g)", value="1g")
            gpu_memory = gr.Textbox(label="GPU显存限制 (如: 1g, 2g)", placeholder="可选")
        
        with gr.Row():
            timeout = gr.Number(label="运行时长限制(秒)", value=3600, minimum=60, maximum=315360000, step=60)
        
        with gr.Row():
            streamable_http = gr.Checkbox(label="启用Streamable HTTP模式", value=False)
            enable_notebook = gr.Checkbox(label="启用Jupyter Notebook", value=False)
        
        with gr.Row():
            external_host = gr.Textbox(label="外部主机名 (--external-host)", placeholder="如: chenbh17-python-mcp.iepose.cn 或 115.190.211.94")
            include_port = gr.Dropdown(choices=["auto", "true", "false"], label="包含端口 (--include-port)", value="true")
        
        start_btn = gr.Button("启动容器")
        start_output = gr.Textbox(label="启动结果", interactive=False)
        
        start_btn.click(
            start_container,
            inputs=[cpu_cores, memory, gpu_memory, timeout, streamable_http, enable_notebook, external_host, include_port],
            outputs=start_output
        )
    
    with gr.Tab("停止容器"):
        gr.Markdown("## 停止运行中的容器")
        
        # 获取容器名称列表用于选择
        def get_container_names():
            try:
                containers = client.containers.list()
                mcp_containers = [c for c in containers if c.name.startswith('python-mcp-container')]
                return [c.name for c in mcp_containers]
            except:
                return []
        
        container_selector = gr.Dropdown(choices=get_container_names(), label="选择要停止的容器")
        refresh_names_btn = gr.Button("刷新容器列表")
        stop_btn = gr.Button("停止容器")
        stop_output = gr.Textbox(label="停止结果", interactive=False)
        
        def update_container_names():
            return gr.update(choices=get_container_names())
        
        refresh_names_btn.click(
            update_container_names,
            outputs=container_selector
        )
        
        stop_btn.click(
            stop_container,
            inputs=container_selector,
            outputs=stop_output
        )
    
    with gr.Tab("终端命令"):
        gr.Markdown("## 在容器中执行终端命令")
        
        with gr.Row():
            terminal_container_selector = gr.Dropdown(choices=get_container_names(), label="选择容器")
            terminal_refresh_btn = gr.Button("刷新容器列表")
        
        terminal_command = gr.Textbox(label="终端命令", placeholder="输入要执行的终端命令")
        terminal_execute_btn = gr.Button("执行命令")
        terminal_output = gr.Textbox(label="执行结果", interactive=False, lines=10, max_lines=20)
        
        def update_terminal_container_names():
            return gr.update(choices=get_container_names())
        
        terminal_refresh_btn.click(
            update_terminal_container_names,
            outputs=terminal_container_selector
        )
        
        def execute_terminal_command(container_name, command):
            """在指定容器中执行终端命令"""
            try:
                if not container_name:
                    return "请选择容器"
                if not command:
                    return "请输入终端命令"
                
                # 获取容器对象
                container = client.containers.get(container_name)
                
                # 执行命令
                result = container.exec_run(command, workdir='/workspace')
                
                if result.exit_code == 0:
                    return result.output.decode('utf-8') if isinstance(result.output, bytes) else result.output
                else:
                    return f"命令执行失败 (退出码: {result.exit_code}):\n{result.output.decode('utf-8') if isinstance(result.output, bytes) else result.output}"
            except Exception as e:
                return f"执行命令时发生错误: {str(e)}"
        
        terminal_execute_btn.click(
            execute_terminal_command,
            inputs=[terminal_container_selector, terminal_command],
            outputs=terminal_output
        )
    
    with gr.Tab("文件列表"):
        gr.Markdown("## 查看容器中的文件")
        
        with gr.Row():
            files_container_selector = gr.Dropdown(choices=get_container_names(), label="选择容器")
            files_refresh_btn = gr.Button("刷新容器列表")
        
        files_path = gr.Textbox(label="路径", placeholder="输入要查看的路径（留空表示根目录）")
        files_list_btn = gr.Button("列出文件")
        files_output = gr.Textbox(label="文件列表", interactive=False, lines=15, max_lines=30)
        
        def update_files_container_names():
            return gr.update(choices=get_container_names())
        
        files_refresh_btn.click(
            update_files_container_names,
            outputs=files_container_selector
        )
        
        def list_container_files(container_name, path):
            """列出指定容器中的文件"""
            try:
                if not container_name:
                    return "请选择容器"
                
                # 获取容器对象
                container = client.containers.get(container_name)
                
                # 构建路径
                target_path = f"/workspace/{path}" if path else "/workspace"
                
                # 执行ls命令
                result = container.exec_run(f"ls -la {target_path}", workdir='/workspace')
                
                if result.exit_code == 0:
                    return result.output.decode('utf-8') if isinstance(result.output, bytes) else result.output
                else:
                    return f"获取文件列表失败 (退出码: {result.exit_code}):\n{result.output.decode('utf-8') if isinstance(result.output, bytes) else result.output}"
            except Exception as e:
                return f"获取文件列表时发生错误: {str(e)}"
        
        files_list_btn.click(
            list_container_files,
            inputs=[files_container_selector, files_path],
            outputs=files_output
        )
    
    with gr.Tab("文件下载"):
        gr.Markdown("## 获取容器中文件的下载链接")
        
        with gr.Row():
            download_container_selector = gr.Dropdown(choices=get_container_names(), label="选择容器")
            download_refresh_btn = gr.Button("刷新容器列表")
        
        download_filepath = gr.Textbox(label="文件路径", placeholder="输入要下载的文件路径（相对于/workspace目录）")
        download_link_btn = gr.Button("获取下载链接")
        download_link_output = gr.Textbox(label="下载链接", interactive=False, lines=3)
        
        def update_download_container_names():
            return gr.update(choices=get_container_names())
        
        download_refresh_btn.click(
            update_download_container_names,
            outputs=download_container_selector
        )
        
        def get_download_link(container_name, filepath):
            """获取指定容器中文件的下载链接"""
            try:
                if not container_name:
                    return "请选择容器"
                if not filepath:
                    return "请输入文件路径"
                
                # 获取容器对象
                container = client.containers.get(container_name)
                
                # 构造下载URL
                # 先尝试从容器环境变量获取外部主机名和端口配置
                container_info = client.api.inspect_container(container.id)
                env_vars = container_info.get('Config', {}).get('Env', [])
                external_host = "localhost"
                include_port_setting = "auto"  # 默认值
                
                for env_var in env_vars:
                    if env_var.startswith('EXTERNAL_HOST='):
                        external_host = env_var.split('=', 1)[1]
                    elif env_var.startswith('INCLUDE_PORT='):
                        include_port_setting = env_var.split('=', 1)[1].lower()
                
                # 判断是否为IP地址格式
                import re
                is_ip_address = re.match(r'^\d+\.\d+\.\d+\.\d+$', external_host) is not None
                
                # 根据设置确定是否包含端口
                include_port = True  # 默认包含端口
                if include_port_setting == "false":
                    include_port = False
                elif include_port_setting == "true":
                    include_port = True
                elif is_ip_address:
                    # 对于IP地址，默认包含端口
                    include_port = True
                else:
                    # 对于域名，默认不包含端口
                    include_port = False
                
                # 获取容器ID（短ID）
                container_id = container.short_id
                
                # 构造下载链接（使用Nginx代理路径）
                if include_port:
                    download_url = f"http://{external_host}:70/{container_id}/download/{filepath.lstrip('/')}"
                else:
                    download_url = f"http://{external_host}/{container_id}/download/{filepath.lstrip('/')}"
                
                return f"下载链接:\n{download_url}\n\n注意：确保文件存在且容器正在运行"
            except Exception as e:
                return f"获取下载链接时发生错误: {str(e)}"
        
        download_link_btn.click(
            get_download_link,
            inputs=[download_container_selector, download_filepath],
            outputs=download_link_output
        )
    
    # 初始化时加载容器列表
    demo.load(
        refresh_containers,
        outputs=[container_table, container_details]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7070)