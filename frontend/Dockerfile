# 使用官方 Node 镜像
FROM node:16

# 设置工作目录
WORKDIR /usr/src/app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制 Vue 项目源代码
COPY . .

# 暴露 Vue 端口
EXPOSE 8080

# 默认命令：启动 Vue 开发服务器
CMD ["npm", "run", "serve"]
