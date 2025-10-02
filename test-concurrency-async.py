import asyncio
import aiohttp
import time

# 异步发送单个请求的函数
async def send_request(session, request_id):
    url = 'http://localhost:3000/orders'
    data = {
        'productId': 2,  # 使用商品ID 1
        'quantity': 1    # 每次购买 1 个
    }

    try:
        async with session.post(url, json=data) as response:
            if 200 <= response.status < 300:  # 接受 2xx 状态码为成功
                result = await response.json()
                print(f"✅ 请求 {request_id} 成功: HTTP {response.status} - {result.get('message', 'OK')}")
                return True
            else:
                text = await response.text()
                print(f"❌ 请求 {request_id} 失败: HTTP {response.status} - {text}")
                return False
    except Exception as e:
        print(f"❌ 请求 {request_id} 失败: {str(e)}")
        return False


def wraper(func):
    async def inner(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"总耗时: {end - start:.2f} 秒")
        return result
    return inner

@wraper
async def simulate_concurrent_requests():
    print("🚀 开始模拟 100 个异步并发请求...")

    start_time = time.time()

    # 创建异步HTTP会话
    async with aiohttp.ClientSession() as session:
        # 创建 100 个并发任务
        tasks = [send_request(session, i + 1) for i in range(10000)]

        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()

    # 处理结果（过滤掉异常）
    valid_results = [r for r in results if not isinstance(r, Exception) and r is not None]
    success_count = sum(1 for result in valid_results if result)
    fail_count = len(valid_results) - success_count
    total_time = end_time - start_time

    print("\n📊 测试结果:")
    print(f"总请求数: {len(valid_results)}")
    print(f"成功数: {success_count}")
    print(f"失败数: {fail_count}")
    print(f"总耗时: {total_time:.2f} 秒")
    if valid_results:
        print(f"平均响应时间: {total_time / len(valid_results):.2f} ms")
    else:
        print("平均响应时间: N/A")

if __name__ == "__main__":
    asyncio.run(simulate_concurrent_requests())