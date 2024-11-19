# 使用官方 Python 镜像
FROM python:3.9

# 设置工作目录
WORKDIR /usr/src/app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
