#!/bin/bash

BASE_DIR="/root/flask-vue/performance-tests"

echo "开始全面测试..."

# 1. 检查环境
echo "1. 检查环境配置..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "❌ curl 未安装"
    exit 1
fi

# 2. 检查目录结构
echo "2. 检查目录结构..."
REQUIRED_DIRS=(
    "$BASE_DIR"
    "$BASE_DIR/bin"
    "$BASE_DIR/results"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ 目录存在: $dir"
    else
        echo "❌ 目录不存在: $dir"
        exit 1
    fi
done

# 3. 测试 Socket 服务
echo "3. 测试 Socket 服务..."
python3 $BASE_DIR/test_socket.py

# 4. 测试程序执行
echo "4. 测试程序执行..."
bash $BASE_DIR/test_program.sh

# 5. 测试 API
echo "5. 测试 API..."
cd $(dirname $BASE_DIR) && python3 backend/tests/test_api.py

# 6. 检查结果
echo "6. 检查最终结果..."
LATEST_RESULT=$(ls -t $BASE_DIR/results | head -n 1)
if [ -n "$LATEST_RESULT" ]; then
    echo "✅ 最新测试结果目录: $LATEST_RESULT"
    ls -l "$BASE_DIR/results/$LATEST_RESULT"
else
    echo "❌ 未找到测试结果"
fi

echo "测试完成!"