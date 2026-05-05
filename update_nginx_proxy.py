#!/usr/bin/env python3
"""
动态Nginx代理配置脚本
自动发现MCP容器并生成Nginx配置
"""

import docker
import time
import subprocess
import os
import re

def get_running_mcp_containers():
    """获取正在运行的MCP容器列表"""
    client = docker.from_env()
    containers = client.containers.list()
    
    mcp_containers = []
    for container in containers:
        # 检查容器名称是否符合MCP容器命名规范
        if container.name.startswith('python-mcp-container'):
            # 获取容器的端口映射信息
            ports = container.attrs['NetworkSettings']['Ports']
            mcp_port = None
            notebook_port = None
            download_port = None
            
            # 查找7000端口的映射
            if '7000/tcp' in ports and ports['7000/tcp']:
                mcp_port = ports['7000/tcp'][0]['HostPort']
            
            # 查找7777端口的映射（Notebook端口）
            if '7777/tcp' in ports and ports['7777/tcp']:
                notebook_port = ports['7777/tcp'][0]['HostPort']
            
            # 查找777端口的映射（下载端口）
            # 注意：实际端口可能是777以上的数字，因为端口冲突时会自动递增
            for port_key in ports:
                if port_key == '777/tcp' and ports[port_key]:
                    download_port = ports[port_key][0]['HostPort']
                    break
            
            if mcp_port:
                mcp_containers.append({
                    'id': container.short_id,
                    'name': container.name,
                    'mcp_port': mcp_port,
                    'notebook_port': notebook_port,
                    'download_port': download_port
                })
    
    return mcp_containers

def generate_nginx_config(containers):
    """生成Nginx配置文件"""
    config = """events {
    worker_connections 1024;
}

http {
    # 使用Docker内置DNS
    resolver 127.0.0.11 valid=30s;
    
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    # 服务器配置
    server {
        listen 70;
        server_name localhost;
        
        # 健康检查端点
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
        
        # 默认页面
        location / {
            return 200 "MCP Nginx Proxy Server\\nAvailable containers:\\n";
        }
"""
    
    # 为每个容器生成代理配置
    for container in containers:
        container_id = container['id']
        mcp_port = container['mcp_port']
        notebook_port = container['notebook_port']
        download_port = container['download_port']
        
        # MCP服务代理配置
        config += f"""
        # 容器 {container_id} 的代理配置 (映射自端口 {mcp_port})
        location /{container_id}/ {{
            proxy_pass http://127.0.0.1:{mcp_port}/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 支持WebSocket
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }}
        
        # 容器 {container_id} 的直接MCP路径
        location /{container_id}/mcp {{
            proxy_pass http://127.0.0.1:{mcp_port}/mcp;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 支持WebSocket和SSE
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
        }}
"""
        
        # 如果容器有下载端口，则添加文件下载代理配置
        if download_port:
            config += f"""
        # 容器 {container_id} 的文件下载路径
        location /{container_id}/download/ {{
            rewrite ^/{container_id}/download/(.*)$ /download/$1 break;
            proxy_pass http://127.0.0.1:{download_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
        }}
"""
        
        # 如果容器有Notebook端口，则添加Notebook代理配置
        if notebook_port:
            config += f"""
        # 容器 {container_id} 的Notebook根路径重定向
        location = /{container_id}/notebook {{
            return 302 /{container_id}/notebook/;
        }}
        
        # 容器 {container_id} 的Notebook静态资源路径
        location ~ /{container_id}/notebook/(static|custom|nbextensions)/ {{
            rewrite ^/{container_id}/notebook/(.*)$ /notebook/$1 break;
            proxy_pass http://127.0.0.1:{notebook_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 静态资源优化
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
            
            # 缓存设置
            expires 1d;
            add_header Cache-Control "public, immutable";
            
            # 确保内容不被修改
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }}
        
        # 容器 {container_id} 的Notebook API路径
        location ~ /{container_id}/notebook/(api/kernels|api/sessions|api/terminals|terminals)/ {{
            rewrite ^/{container_id}/notebook/(.*)$ /notebook/$1 break;
            proxy_pass http://127.0.0.1:{notebook_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket支持（关键）
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }}
        
        # 容器 {container_id} 的Notebook路径
        location /{container_id}/notebook/ {{
            rewrite ^/{container_id}/notebook/(.*)$ /notebook/$1 break;
            proxy_pass http://127.0.0.1:{notebook_port};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 解决Notebook白屏问题的关键配置
            proxy_buffering off;
            proxy_request_buffering off;
            proxy_http_version 1.1;
            
            # WebSocket支持
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
            
            # 处理重定向和路径
            proxy_redirect ~^/notebook/(.*) /{container_id}/notebook/$1;
            proxy_redirect http://127.0.0.1:{notebook_port}/notebook/ /{container_id}/notebook/;
            proxy_redirect http://localhost:{notebook_port}/notebook/ /{container_id}/notebook/;
        }}
"""
    
    config += """
    }
}
"""
    return config

def write_nginx_config(config, filepath='/etc/nginx/nginx.conf'):
    """写入Nginx配置文件"""
    try:
        with open(filepath, 'w') as f:
            f.write(config)
        print(f"Nginx配置已写入到 {filepath}")
        return True
    except Exception as e:
        print(f"写入Nginx配置失败: {e}")
        return False

def reload_nginx():
    """重新加载Nginx配置"""
    try:
        result = subprocess.run(['nginx', '-s', 'reload'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Nginx配置重新加载成功")
            return True
        else:
            print(f"Nginx重新加载失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"执行nginx重新加载命令失败: {e}")
        return False

def test_nginx_config():
    """测试Nginx配置语法"""
    try:
        result = subprocess.run(['nginx', '-t'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Nginx配置语法检查通过")
            return True
        else:
            print(f"Nginx配置语法检查失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"执行nginx配置测试命令失败: {e}")
        return False

def main():
    """主函数"""
    print("开始生成Nginx代理配置...")
    
    # 获取运行中的MCP容器
    containers = get_running_mcp_containers()
    print(f"发现 {len(containers)} 个运行中的MCP容器")
    
    # 生成Nginx配置
    config = generate_nginx_config(containers)
    
    # 写入配置文件
    if write_nginx_config(config):
        # 测试配置语法
        if test_nginx_config():
            # 重新加载Nginx
            reload_nginx()
            
            # 输出访问信息
            print("\n代理配置已完成！")
            print("访问方式:")
            for container in containers:
                print(f"  容器 {container['id']} 的MCP服务: http://localhost:70/{container['id']}/mcp")
                print(f"  容器 {container['id']} 的API服务: http://localhost:70/{container['id']}/")
                print(f"    (映射自主机端口 {container['mcp_port']})")
                # 如果有Notebook端口，也显示Notebook访问信息
                if container['notebook_port']:
                    print(f"  容器 {container['id']} 的Notebook服务: http://localhost:70/{container['id']}/notebook")
                    print(f"    (映射自主机端口 {container['notebook_port']})")
                # 如果有下载端口，也显示下载访问信息
                if container['download_port']:
                    print(f"  容器 {container['id']} 的文件下载服务: http://localhost:70/{container['id']}/download")
                    print(f"    (映射自主机端口 {container['download_port']})")
        else:
            print("Nginx配置语法检查失败，请检查配置文件")
    else:
        print("写入Nginx配置文件失败")

if __name__ == "__main__":
    main()