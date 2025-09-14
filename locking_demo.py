import redis.sentinel
import time
import uuid
import os

# --- 配置 ---
SENTINEL_HOSTS = [('localhost', 26379), ('localhost', 26380), ('localhost', 26381)]
MASTER_NAME = 'mymaster'
SOCKET_TIMEOUT = 5 # 将超时时间延长到 5 秒
LOCK_KEY = 'my-distributed-lock'
LOCK_TIMEOUT_MS = 10000  # 锁的过期时间（毫秒）

# --- Lua 脚本，用于安全地释放锁 ---
LUA_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

try:
    # --- 连接 Sentinel 并获取主节点客户端 ---
    sentinel = redis.sentinel.Sentinel(SENTINEL_HOSTS, socket_timeout=SOCKET_TIMEOUT)
    master = sentinel.master_for(MASTER_NAME, socket_timeout=SOCKET_TIMEOUT)

    # --- 主循环 ---
    my_random_value = str(uuid.uuid4())
    pid = os.getpid()
    print(f"[进程 {pid}] 已启动，我的唯一值是 {my_random_value[:6]}...")

    while True:
        print(f"\n[进程 {pid}] 尝试获取锁...")
        # 尝试使用 SET NX PX 原子性地加锁
        if master.set(LOCK_KEY, my_random_value, nx=True, px=LOCK_TIMEOUT_MS):
            print(f"[进程 {pid}] ✅ 成功获取锁！将持有 {LOCK_TIMEOUT_MS / 1000} 秒。")
            try:
                # 模拟持有锁执行关键任务
                print(f"[进程 {pid}] 正在执行关键任务...")
                time.sleep(5)
                print(f"[进程 {pid}] 关键任务执行完毕。")
            finally:
                # 任务完成后，安全地释放锁
                print(f"[进程 {pid}] 准备释放锁...")
                master.eval(LUA_RELEASE_LOCK_SCRIPT, 1, LOCK_KEY, my_random_value)
                print(f"[进程 {pid}] ✅ 锁已释放！")
                # 释放后等待一段时间再重新竞争
                time.sleep(3)
        else:
            # 加锁失败，等待后重试
            print(f"[进程 {pid}] 锁被占用，1 秒后重试...")
            time.sleep(1)

except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
    print(f"❌ 连接或超时错误: {e}")
    print("\n💡提示：请确认你的 /etc/hosts 文件中是否已添加 '127.0.0.1 redis-master' 这一行，并检查防火墙设置。")
except Exception as e:
    print(f"❌ 发生了未知错误: {e}")