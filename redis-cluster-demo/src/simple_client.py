#!/usr/bin/env python3
"""
Redis 集群客户端入门版

文件目的：
本脚本提供一个极简的 Redis 集群客户端，专为初学者设计。
它演示了如何连接到集群、执行基本的数据操作（增删改查），
以及如何处理 Redis 集群中最重要的概念之一：MOVED 重定向。

适合人群：
- Redis 集群初学者
- 希望理解集群客户端基本工作原理的开发者
"""

try:
    import redis
    from redis.exceptions import ResponseError
    REDIS_AVAILABLE = True
except ImportError:
    print("⚠️ 需要安装redis包: pip install redis")
    REDIS_AVAILABLE = False


class SimpleClusterClient:
    """
    一个简单的 Redis 集群客户端。

    本类通过连接到集群的多个节点，提供一个统一的接口来操作数据。
    它会处理基本的 'MOVED' 重定向，这是与 Redis 集群交互的关键。
    """
    
    def __init__(self):
        """
        初始化客户端，并连接到所有预定义的 Redis 节点。
        """
        if not REDIS_AVAILABLE:
            raise ImportError("无法启动客户端，因为 'redis' 库未安装。")
        
        # 定义集群的节点信息。在实际应用中，这些信息通常来自配置文件。
        self.nodes = {
            'node1': {'host': 'localhost', 'port': 7001},
            'node2': {'host': 'localhost', 'port': 7002},
            'node3': {'host': 'localhost', 'port': 7003}
        }
        
        # 用于存储每个节点的 redis 连接对象
        self.clients = {}
        self._connect_to_all_nodes()
    
    def _connect_to_all_nodes(self):
        """
        遍历所有节点信息，并尝试建立连接。
        """
        print("🔗 正在尝试连接到 Redis 集群的所有节点...")
        
        for node_name, node_info in self.nodes.items():
            try:
                # 创建 Redis 连接实例
                client = redis.Redis(
                    host=node_info['host'],
                    port=node_info['port'],
                    decode_responses=True,  # 自动将 Redis 返回的 bytes 解码为字符串
                    socket_timeout=5        # 设置超时时间，避免长时间等待
                )
                
                # 发送 PING 命令测试连接是否成功
                client.ping()
                self.clients[node_name] = client
                print(f"  ✅ 成功连接到节点 '{node_name}' (地址: {node_info['host']}:{node_info['port']})")
                
            except Exception as e:
                print(f"  ❌ 连接节点 '{node_name}' 失败: {e}")
        
        if not self.clients:
            raise ConnectionError("❌ 致命错误：无法连接到任何一个 Redis 节点。请检查集群状态。" )
        
        print(f"✅ 已成功连接 {len(self.clients)} 个节点.\n")
    
    def _get_initial_client(self):
        """
        选择一个初始节点来发送命令。

        这是一个非常简单的策略：总是选择第一个可用的节点。
        更复杂的客户端会使用更智能的策略（例如，随机或轮询）。
        """
        return list(self.clients.values())[0]
    
    def _handle_redirect(self, error_message: str, operation_func):
        """
        处理 Redis 集群的 MOVED 重定向错误。

        背景知识：
        Redis 集群会将数据分散存储在不同的节点上。当你向一个节点发送命令，
        但这个命令操作的键实际上存储在另一个节点时，服务器会返回一个 'MOVED' 错误。
        这个错误会告诉你正确的节点地址。客户端需要根据这个信息，重新向正确的节点发送命令。

        本函数的工作流程：
        1. 解析错误信息，格式通常是 "MOVED <槽位号> <正确节点的IP:端口>"。
        2. 从中提取出正确节点的地址（例如 "redis-node-2:6379"）。
        3. 根据地址找到我们已经建立好的连接客户端。
        4. 使用正确的客户端重新执行原始操作。
        """
        try:
            # 从错误信息 "MOVED 12345 redis-node-2:6379" 中提取 "redis-node-2:6379"
            parts = error_message.strip().split()
            if len(parts) >= 2:
                target_node_info = parts[1]
                
                # 根据节点名找到对应的客户端
                if 'redis-node-1' in target_node_info:
                    print("  ➡️  检测到重定向，将命令发送到 node1...")
                    return operation_func(self.clients['node1'])
                elif 'redis-node-2' in target_node_info:
                    print("  ➡️  检测到重定向，将命令发送到 node2...")
                    return operation_func(self.clients['node2'])
                elif 'redis-node-3' in target_node_info:
                    print("  ➡️  检测到重定向，将命令发送到 node3...")
                    return operation_func(self.clients['node3'])
            
            # 如果无法从错误信息中识别出目标节点，就用第一个节点重试
            print("  ⚠️ 无法解析重定向信息，将使用默认节点重试...")
            return operation_func(self._get_initial_client())
            
        except Exception as e:
            # 如果重定向处理过程中出现任何问题，就抛出异常
            raise ConnectionError(f"处理重定向失败: {error_message}, 内部错误: {e}")
    
    def set(self, key: str, value: str) -> bool:
        """
        向集群中设置一个键值对。

        Args:
            key (str): 要设置的键。
            value (str): 要设置的值。

        Returns:
            bool: 如果设置成功，返回 True。
        """
        # 定义要执行的具体操作
        def operation(client):
            return client.set(key, value)
        
        try:
            # 首先，尝试使用初始节点执行命令
            initial_client = self._get_initial_client()
            return operation(initial_client)
            
        except ResponseError as e:
            # 如果收到响应错误，检查是否是 MOVED 重定向
            if "MOVED" in str(e):
                return self._handle_redirect(str(e), operation)
            else:
                # 如果是其他错误，直接抛出
                raise e
    
    def get(self, key: str) -> str:
        """
        从集群中获取一个键的值。

        Args:
            key (str): 要获取的键。

        Returns:
            str: 键对应的值。如果键不存在，返回 None。
        """
        def operation(client):
            return client.get(key)
        
        try:
            initial_client = self._get_initial_client()
            return operation(initial_client)
            
        except ResponseError as e:
            if "MOVED" in str(e):
                return self._handle_redirect(str(e), operation)
            else:
                raise e
    
    def delete(self, key: str) -> bool:
        """
        从集群中删除一个键。

        Args:
            key (str): 要删除的键。

        Returns:
            bool: 如果成功删除，返回 True。
        """
        def operation(client):
            # client.delete 返回删除的键的数量 (0 或 1)
            return client.delete(key) > 0
        
        try:
            initial_client = self._get_initial_client()
            return operation(initial_client)
            
        except ResponseError as e:
            if "MOVED" in str(e):
                return self._handle_redirect(str(e), operation)
            else:
                raise e
    
    def exists(self, key: str) -> bool:
        """
        检查一个键是否存在于集群中。

        Args:
            key (str): 要检查的键。

        Returns:
            bool: 如果键存在，返回 True。
        """
        def operation(client):
            # client.exists 返回存在的键的数量 (0 或 1)
            return client.exists(key) > 0
        
        try:
            initial_client = self._get_initial_client()
            return operation(initial_client)
            
        except ResponseError as e:
            if "MOVED" in str(e):
                return self._handle_redirect(str(e), operation)
            else:
                raise e
    
    def get_all_keys(self) -> list:
        """
        获取集群中所有节点上的所有键。

        注意：
        在生产环境中，'KEYS *' 是一个危险的操作，因为它会阻塞服务器。
        这个函数仅用于演示和调试目的。

        Returns:
            list: 包含所有键的列表。
        """
        all_keys = set()  # 使用集合来自动处理重复的键
        
        print("🔍 正在从所有节点获取键列表...")
        for node_name, client in self.clients.items():
            try:
                # 从当前节点获取所有键
                keys_on_node = client.keys('*')
                all_keys.update(keys_on_node)
                print(f"  📊 从节点 '{node_name}' 获取了 {len(keys_on_node)} 个键")
                
            except Exception as e:
                print(f"  ❌ 从节点 '{node_name}' 获取键列表失败: {e}")
        
        return list(all_keys)


def run_demonstration():
    """
    运行一个完整的演示，展示客户端的各项功能。
    """
    print("🎯 Redis 集群客户端基础功能演示")
    print("=" * 40)
    
    try:
        # 步骤 1: 初始化客户端并连接到集群
        print("第一步：初始化客户端...")
        client = SimpleClusterClient()
        
        # 步骤 2: 写入一些测试数据
        # 这些键会根据 Redis 的哈希算法，被分散存储到不同的节点上。
        print("第二步：写入测试数据...")
        test_data = {
            "user:1": "Alice",
            "user:2": "Bob", 
            "product:123": "Laptop",
            "session:xyz": "active"
        }
        
        for key, value in test_data.items():
            if client.set(key, value):
                print(f"  ✅ 写入成功: {key} = '{value}'")
            else:
                print(f"  ❌ 写入失败: {key}")
        print()
        
        # 步骤 3: 读取刚才写入的数据
        # 客户端可能会遇到 MOVED 重定向，但 _handle_redirect 函数会自动处理。
        print("第三步：读取数据...")
        for key in test_data.keys():
            value = client.get(key)
            print(f"  📋 读取: {key} -> '{value}'")
        print()
        
        # 步骤 4: 检查某些键是否存在
        print("第四步：检查键是否存在...")
        keys_to_check = ["user:1", "user:999", "product:123"]
        for key in keys_to_check:
            status = "存在" if client.exists(key) else "不存在"
            print(f"  🔍 检查: {key} -> {status}")
        print()
        
        # 步骤 5: 获取集群中所有的键
        print("第五步：获取集群中的所有键...")
        all_keys = client.get_all_keys()
        print(f"  🗝️  集群中的总键数: {len(all_keys)}")
        print("  🔑  键列表: ", sorted(all_keys))
        print()
        
        # 步骤 6: 删除部分数据
        print("第六步：删除数据...")
        keys_to_delete = ["user:2", "session:xyz"]
        for key in keys_to_delete:
            if client.delete(key):
                print(f"  🗑️  成功删除: {key}")
            else:
                print(f"  ❌ 删除失败: {key}")
        print()
        
        # 步骤 7: 再次检查，验证删除结果
        print("第七步：验证删除结果...")
        final_keys = client.get_all_keys()
        print(f"  🗝️  删除后的总键数: {len(final_keys)}")
        print("  🔑  剩余键列表: ", sorted(final_keys))
        
        print("\n🎉 演示成功完成!")
        print("\n💡 通过本演示，你学到了:")
        print("  1. 如何连接到一个 Redis 集群。")
        print("  2. 如何执行基本的 SET, GET, DELETE, EXISTS 操作。")
        print("  3. 客户端如何通过处理 MOVED 重定向来与集群正确交互。")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        print("\n💡 请检查以下几点:")
        print("  - Redis 集群是否已通过 './redis-cluster.sh start' 成功启动？")
        print("  - Docker 容器是否正在运行？")
        print("  - 端口 7001, 7002, 7003 是否没有被其他程序占用？")


# 当这个脚本被直接执行时，运行演示函数
if __name__ == "__main__":
    if not REDIS_AVAILABLE:
        # 如果 redis 库没有安装，不继续执行
        pass
    else:
        try:
            run_demonstration()
        except KeyboardInterrupt:
            print("\n\n⏹️  用户手动中断了程序。")
        except Exception as e:
            print(f"\n❌ 程序出现未处理的异常: {e}")
