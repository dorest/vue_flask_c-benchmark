# 使用官方 Python 镜像
FROM python:3.9

# 设置工作目录
WORKDIR /usr/src/app

# 复制依赖文件
COPY requirements.txt ./

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制 Flask 应用代码
COPY . .

# 暴露 Flask 端口
EXPOSE 5000

# 默认命令：启动 Flask 应用
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
