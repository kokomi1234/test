"""
示例依赖与运行说明：

1) 此项目推荐使用虚拟环境（项目里可能有 `.venv`）。
2) 安装依赖：
    /Users/a1/Desktop/redis-sentinel-demo/.venv/bin/python -m pip install -r requirements.txt
    或（全局/其他环境）:
    python -m pip install redis>=4.9.0
3) 用项目虚拟环境运行示例：
    /Users/a1/Desktop/redis-sentinel-demo/.venv/bin/python client_demo.py

此脚本使用 redis-py (redis) 包中的 Sentinel 支持：导入为 `import redis.sentinel`。
"""

import redis.sentinel
import time
import sys

# --- 配置 ---
SENTINEL_HOSTS = [('localhost', 26379), ('localhost', 26380), ('localhost', 26381)]
MASTER_NAME = 'mymaster'
SOCKET_TIMEOUT = 5 # 将超时时间延长到 5 秒

try:
    # --- 连接 Sentinel ---
    print("正在连接到 Sentinel 服务器...")
    sentinel = redis.sentinel.Sentinel(SENTINEL_HOSTS, socket_timeout=SOCKET_TIMEOUT)

    # --- 获取主节点客户端 ---
    print("正在通过 Sentinel 获取主节点客户端...")
    master = sentinel.master_for(MASTER_NAME, socket_timeout=SOCKET_TIMEOUT, decode_responses=True)

    # --- 写测试 ---
    print("\n--- 开始主节点写入测试 ---")
    key = 'mykey'
    value = f'hello_from_sentinel_client_{time.time()}'

    print(f"1. 向主节点写入: SET {key} '{value}'")
    master.set(key, value)
    print("✅ 写入成功！")

    # --- 读测试 ---
    print(f"2. 从主节点直接读回: GET {key}")
    retrieved_value = master.get(key)

    if retrieved_value == value:
        print(f"✅ 成功! 读到的值与写入的值一致: '{retrieved_value}'")
    else:
        print(f"❌ 失败! 读写的值不一致。读到: {retrieved_value}")
        sys.exit(1)

except redis.exceptions.MasterDownError as e:
    print(f"❌ 错误: Sentinel 无法找到名为 '{MASTER_NAME}' 的主节点。 {e}")
except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
    print(f"❌ 连接或超时错误: {e}")
    print("\n💡提示：这个错误通常意味着你的电脑无法解析 'redis-master' 主机名或网络连接被阻止。")
    print("请确认你的 /etc/hosts 文件中是否已添加 '127.0.0.1 redis-master' 这一行，并检查防火墙设置。")
except Exception as e:
    print(f"❌ 发生了未知错误: {e}")