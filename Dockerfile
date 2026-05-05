FROM python:3.11-slim

# 配置APT阿里镜像源
RUN echo "deb https://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装系统依赖和常用工具
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmariadb-dev \
    libsasl2-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    procps \
    net-tools \
    dnsutils \
    curl \
    wget \
    vim \
    nano \
    telnet \
    iputils-ping \
    htop \
    tree \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 配置pip阿里镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 安装基础科学计算和数据处理包
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scipy \
    statsmodels \
    openpyxl

# 安装机器学习和深度学习框架
RUN pip install --no-cache-dir \
    scikit-learn \
    scikit-optimize \
    lightgbm \
    xgboost \
    tensorflow \
    keras

# 安装自然语言处理和文本处理包
RUN pip install --no-cache-dir \
    jieba

# 安装数据可视化包
RUN pip install --no-cache-dir \
    matplotlib \
    seaborn \
    plotly

# 安装数据库连接和数据处理包
RUN pip install --no-cache-dir \
    pymysql \
    pyhive \
    clickhouse_connect \
    sqlalchemy

# 安装网络和通信相关包
RUN pip install --no-cache-dir \
    thrift \
    thrift_sasl \
    paramiko

# 安装工具和实用程序包
RUN pip install --no-cache-dir \
    tqdm \
    joblib \
    Pillow

# 安装MCP服务器相关依赖
RUN pip install --no-cache-dir \
    flask \
    requests \
    mcp \
    fastapi \
    uvicorn \
    starlette \
    httpx \
    pydantic 

# 安装Jupyter Notebook及相关依赖
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    ipykernel \
    ipython

# 安装Docker SDK用于容器管理
RUN pip install --no-cache-dir \
    docker

# 安装额外的数据科学和可视化包
RUN pip install --no-cache-dir \
    ipywidgets

# 配置Jupyter
RUN mkdir -p /root/.jupyter

# 创建Jupyter配置文件
RUN echo "c.ServerApp.token = ''" > /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.password = ''" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.open_browser = False" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.allow_root = True" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.port = 7777" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.root_dir = '/workspace'" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.disable_check_xsrf = True" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.allow_origin = '*'" >> /root/.jupyter/jupyter_server_config.py && \
    echo "c.ServerApp.base_url = '/notebook'" >> /root/.jupyter/jupyter_server_config.py

# 创建目录用于存储用户代码
RUN mkdir -p /workspace

# 设置环境变量，使bash启动时进入/workspace目录
ENV ENV="/etc/profile"

# 创建profile文件，设置bash启动目录
RUN echo "cd /workspace" >> /etc/profile

# 安装Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# 创建Nginx日志目录
RUN mkdir -p /var/log/nginx

# 复制MCP服务器代码
COPY mcp_server.py /app/mcp_server.py
COPY update_nginx_proxy.py /app/update_nginx_proxy.py
COPY nginx_proxy_runner.sh /app/nginx_proxy_runner.sh

# 复制 cbhpacks wheel 包并安装
COPY cbhpacks-1.2.8-py3-none-any.whl /app/cbhpacks-1.2.8-py3-none-any.whl
RUN pip install --no-cache-dir /app/cbhpacks-1.2.8-py3-none-any.whl

# 复制 cbhpacks 模块和工具
COPY cbhpacks /app/cbhpacks
COPY cbhpacks_mcp_tools.py /app/cbhpacks_mcp_tools.py

# 暴露端口
EXPOSE 7000
EXPOSE 7777
EXPOSE 777

# 启动脚本
COPY start_services.sh /app/start_services.sh
RUN chmod +x /app/start_services.sh

# 设置环境变量，使bash启动时进入/workspace目录
ENV ENV="/etc/profile"

# 创建profile文件，设置bash启动目录
RUN echo "cd /workspace" >> /etc/profile

# 设置默认命令
CMD ["/app/start_services.sh"]