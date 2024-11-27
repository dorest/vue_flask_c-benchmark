#!/bin/bash

BASE_DIR="/root/flask-vue/performance-tests"
TEST_DIR="$BASE_DIR/test_results"
mkdir -p "$TEST_DIR"

echo "1. 测试程序权限..."
if [ -x "$BASE_DIR/bin/test_program" ]; then
    echo "✅ 测试程序可执行"
else
    echo "❌ 测试程序权限不足"
    exit 1
fi

echo "2. 测试程序执行..."
$BASE_DIR/bin/test_program \
    --config '{"test":"demo"}' \
    --output "$TEST_DIR/test_run"

if [ $? -eq 0 ]; then
    echo "✅ 测试程序执行成功"
else
    echo "❌ 测试程序执行失败"
    exit 1
fi

# ... 其他检查 ...