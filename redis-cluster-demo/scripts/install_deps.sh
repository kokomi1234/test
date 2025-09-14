#!/bin/bash

# Redis集群现代客户端依赖安装脚本
# 安装最新版本的redis-py库

echo "🚀 Redis集群现代客户端依赖安装"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未找到，请先安装Python3"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3未找到，请先安装pip"
    exit 1
fi

echo "📦 正在安装Redis客户端依赖..."

# 安装最新的redis-py库（支持集群）
pip3 install redis

# 检查安装结果
if python3 -c "import redis.cluster; print('✅ redis-py集群支持已安装')" 2>/dev/null; then
    echo "🎉 依赖安装成功！"
    echo ""
    echo "📋 现在可以运行以下命令:"
    echo "   python3 modern_cluster_client.py"
    echo ""
    echo "💡 或者直接在Python中使用:"
    echo "   from redis.cluster import RedisCluster"
else
    echo "❌ 安装验证失败，请检查错误信息"
    exit 1
fi