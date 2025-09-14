#!/usr/bin/env python3
"""
Redis 集群客户端 - 简单重定向处理版本

设计理念：
- 不主动计算槽位，让 Redis 集群自己处理路由
- 简单发送命令到任意节点，处理集群的重定向响应
- 符合 Redis 集群的原始设计思路
"""

try:
    import redis
    from redis.exceptions import ResponseError, ConnectionError, MovedError, AskError
    REDIS_AVAILABLE = True
except ImportError:
    print("⚠️ 需要安装redis包: pip install redis")
    REDIS_AVAILABLE = False


class RedirectClusterClient:
    """Redis 集群客户端 - 重定向处理版本"""
    
    def __init__(self):
        """初始化集群客户端"""
        if not REDIS_AVAILABLE:
            raise ImportError("请先安装redis包: pip install redis")
        
        # 集群节点信息
        self.nodes = {
            'node1': {'host': 'localhost', 'port': 7001},
            'node2': {'host': 'localhost', 'port': 7002}, 
            'node3': {'host': 'localhost', 'port': 7003}
        }
        
        # 容器名到端口的映射（用于处理重定向）
        self.container_to_port = {
            'redis-node-1': 7001,
            'redis-node-2': 7002,
            'redis-node-3': 7003
        }
        
        # 连接所有节点
        self.clients = {}
        self._connect_nodes()
        
        # 当前使用的客户端索引（简单轮询）
        self.current_client_index = 0
    
    def _connect_nodes(self):
        """连接所有Redis节点"""
        print("🔗 连接Redis集群...")
        
        for node_name, node_info in self.nodes.items():
            try:
                client = redis.Redis(
                    host=node_info['host'],
                    port=node_info['port'],
                    decode_responses=True,
                    socket_timeout=5
                )
                
                # 测试连接
                client.ping()
                self.clients[node_name] = client
                print(f"  ✅ {node_name}: localhost:{node_info['port']}")
                
            except Exception as e:
                print(f"  ❌ {node_name}: 连接失败 - {e}")
        
        if not self.clients:
            raise Exception("❌ 无法连接任何Redis节点")
        
        print(f"✅ 成功连接 {len(self.clients)} 个节点\n")
    
    def _get_any_client(self):
        """获取任意一个可用的客户端（简单轮询）"""
        client_list = list(self.clients.values())
        client = client_list[self.current_client_index % len(client_list)]
        self.current_client_index += 1
        return client
    
    def _parse_redirect(self, error_msg: str):
        """解析重定向信息
        
        Redis 返回的重定向格式：
        - MOVED: "MOVED 12345 redis-node-2:6379"
        - ASK: "ASK 12345 redis-node-2:6379"  
        - 或者直接: "12345 redis-node-2:6379"
        """
        try:
            # 移除可能的 MOVED 或 ASK 前缀
            parts = error_msg.replace('MOVED ', '').replace('ASK ', '').strip().split()
            
            if len(parts) >= 2:
                slot = int(parts[0])
                target_address = parts[1]
                
                # 解析目标地址
                if ':' in target_address:
                    container_name, port = target_address.rsplit(':', 1)
                    
                    # 查找对应的外部端口
                    external_port = self.container_to_port.get(container_name)
                    if external_port:
                        return external_port
            
            return None
            
        except Exception as e:
            print(f"    ❌ 解析重定向失败: {e}")
            return None
    
    def _get_client_by_port(self, port: int):
        """根据端口号获取客户端"""
        for node_name, node_info in self.nodes.items():
            if node_info['port'] == port:
                return self.clients.get(node_name)
        return None
    
    def _execute_command(self, command_func, max_redirects: int = 5):
        """执行命令并处理重定向
        
        设计思路：
        1. 随机选择一个节点发送命令
        2. 如果收到重定向，解析目标节点并重试
        3. 让 Redis 集群自己决定数据应该在哪个节点
        """
        for attempt in range(max_redirects):
            try:
                # 1. 选择任意一个节点发送命令
                client = self._get_any_client()
                return command_func(client)
                
            except (MovedError, AskError) as e:
                # 2. 处理 Redis 集群的重定向
                error_msg = str(e)
                print(f"  🔄 收到重定向 (尝试 {attempt + 1}): {error_msg}")
                
                # 解析重定向目标
                target_port = self._parse_redirect(error_msg)
                if target_port:
                    target_client = self._get_client_by_port(target_port)
                    if target_client:
                        try:
                            # 对于 ASK 重定向，需要先发送 ASKING
                            if isinstance(e, AskError):
                                target_client.execute_command('ASKING')
                            
                            result = command_func(target_client)
                            print(f"    ✅ 重定向成功")
                            return result
                            
                        except Exception as retry_error:
                            print(f"    ⚠️ 重定向后执行失败: {retry_error}")
                            if attempt == max_redirects - 1:
                                raise retry_error
                    else:
                        print(f"    ❌ 找不到端口 {target_port} 对应的客户端")
                else:
                    print(f"    ❌ 无法解析重定向信息")
                
                if attempt == max_redirects - 1:
                    raise e
                        
            except ResponseError as e:
                # 3. 处理其他可能的重定向格式
                error_msg = str(e)
                if any(char.isdigit() for char in error_msg) and ':' in error_msg:
                    print(f"  🔄 检测到可能的重定向 (尝试 {attempt + 1}): {error_msg}")
                    
                    target_port = self._parse_redirect(error_msg)
                    if target_port:
                        target_client = self._get_client_by_port(target_port)
                        if target_client:
                            try:
                                result = command_func(target_client)
                                print(f"    ✅ 重定向成功")
                                return result
                            except Exception as retry_error:
                                print(f"    ⚠️ 重定向后执行失败: {retry_error}")
                                if attempt == max_redirects - 1:
                                    raise retry_error
                
                # 如果不是重定向，直接抛出异常
                raise e
            
            except Exception as e:
                if attempt == max_redirects - 1:
                    raise e
                print(f"  ⚠️ 尝试 {attempt + 1} 失败: {e}")
        
        raise Exception(f"命令执行失败，已重试 {max_redirects} 次")
    
    # =================== 基础 CRUD 操作 ===================
    
    def set(self, key: str, value: str, ex: int = None) -> bool:
        """设置键值对"""
        def command(client):
            if ex:
                return client.setex(key, ex, value)
            else:
                return client.set(key, value)
        
        return self._execute_command(command)
    
    def get(self, key: str) -> str:
        """获取键值"""
        def command(client):
            return client.get(key)
        
        return self._execute_command(command)
    
    def delete(self, key: str) -> bool:
        """删除键"""
        def command(client):
            return client.delete(key) > 0
        
        return self._execute_command(command)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        def command(client):
            return client.exists(key) > 0
        
        return self._execute_command(command)
    
    def incr(self, key: str) -> int:
        """自增计数器"""
        def command(client):
            return client.incr(key)
        
        return self._execute_command(command)
    
    # =================== 哈希操作 ===================
    
    def hset(self, name: str, key: str, value: str) -> bool:
        """设置哈希字段"""
        def command(client):
            return client.hset(name, key, value)
        
        return self._execute_command(command)
    
    def hget(self, name: str, key: str) -> str:
        """获取哈希字段"""
        def command(client):
            return client.hget(name, key)
        
        return self._execute_command(command)
    
    def hgetall(self, name: str) -> dict:
        """获取所有哈希字段"""
        def command(client):
            return client.hgetall(name)
        
        return self._execute_command(command)
    
    # =================== 列表操作 ===================
    
    def lpush(self, name: str, *values) -> int:
        """左推入列表"""
        def command(client):
            return client.lpush(name, *values)
        
        return self._execute_command(command)
    
    def rpush(self, name: str, *values) -> int:
        """右推入列表"""
        def command(client):
            return client.rpush(name, *values)
        
        return self._execute_command(command)
    
    def lpop(self, name: str) -> str:
        """左弹出列表"""
        def command(client):
            return client.lpop(name)
        
        return self._execute_command(command)
    
    def llen(self, name: str) -> int:
        """获取列表长度"""
        def command(client):
            return client.llen(name)
        
        return self._execute_command(command)
    
    # =================== 集合操作 ===================
    
    def sadd(self, name: str, *values) -> int:
        """添加到集合"""
        def command(client):
            return client.sadd(name, *values)
        
        return self._execute_command(command)
    
    def smembers(self, name: str) -> set:
        """获取集合成员"""
        def command(client):
            return client.smembers(name)
        
        return self._execute_command(command)
    
    # =================== 实用方法 ===================
    
    def get_all_keys(self) -> list:
        """获取集群中所有的键"""
        all_keys = []
        
        for node_name, client in self.clients.items():
            try:
                keys = client.keys('*')
                all_keys.extend(keys)
                print(f"  📊 {node_name}: {len(keys)} 个键")
                
            except Exception as e:
                print(f"  ❌ {node_name}: 获取失败 - {e}")
        
        return list(set(all_keys))  # 去重
    
    def set_many(self, data_dict: dict):
        """批量设置键值对"""
        print(f"📝 批量设置 {len(data_dict)} 个键值对:")
        
        for key, value in data_dict.items():
            try:
                self.set(key, str(value))
                print(f"  ✅ {key} = {value}")
            except Exception as e:
                print(f"  ❌ {key} 设置失败: {e}")
    
    def get_cluster_stats(self) -> dict:
        """获取集群统计信息"""
        stats = {
            'total_keys': 0,
            'distribution': {},
            'nodes': len(self.clients)
        }
        
        print("📊 统计集群信息:")
        
        for node_name, client in self.clients.items():
            try:
                keys = client.keys('*')
                key_count = len(keys)
                stats['total_keys'] += key_count
                stats['distribution'][node_name] = key_count
                
                port = self.nodes[node_name]['port']
                print(f"  📈 {node_name} (:{port}): {key_count} 个键")
                
            except Exception as e:
                print(f"  ❌ {node_name}: 统计失败 - {e}")
                stats['distribution'][node_name] = 0
        
        return stats


def demo():
    """演示Redis集群重定向处理"""
    print("🎯 Redis集群重定向处理演示")
    print("让 Redis 自己决定数据路由，我们只处理重定向")
    print("=" * 50)
    
    try:
        # 1. 连接集群
        client = RedirectClusterClient()
        
        # 2. 基础操作演示
        print("📝 1. 基础 CRUD 操作")
        
        # 这些操作会被 Redis 自动路由到正确的节点
        test_data = {
            "user:alice": "Alice用户信息", 
            "user:bob": "Bob用户信息",
            "session:12345": "用户会话数据",
            "cache:product:1": "产品缓存",
            "counter:visits": "100"
        }
        
        client.set_many(test_data)
        
        print("\n📖 2. 读取数据")
        for key in list(test_data.keys())[:3]:
            try:
                value = client.get(key)
                print(f"  📋 {key} = {value}")
            except Exception as e:
                print(f"  ❌ {key} 读取失败: {e}")
        
        # 3. 哈希操作
        print("\n🗃️ 3. 哈希表操作")
        try:
            client.hset("profile:charlie", "name", "Charlie")
            client.hset("profile:charlie", "age", "25")
            client.hset("profile:charlie", "city", "Shanghai")
            
            profile = client.hgetall("profile:charlie")
            print(f"  👤 用户资料: {profile}")
            
        except Exception as e:
            print(f"  ❌ 哈希操作失败: {e}")
        
        # 4. 列表操作
        print("\n📋 4. 列表操作")
        try:
            client.rpush("tasks", "任务1", "任务2", "任务3")
            length = client.llen("tasks")
            print(f"  📝 任务队列长度: {length}")
            
            task = client.lpop("tasks")
            print(f"  ✅ 完成任务: {task}")
            
        except Exception as e:
            print(f"  ❌ 列表操作失败: {e}")
        
        # 5. 计数器操作
        print("\n🔢 5. 计数器操作")
        try:
            for i in range(3):
                count = client.incr("page_views")
                print(f"  📊 页面访问次数: {count}")
                
        except Exception as e:
            print(f"  ❌ 计数器操作失败: {e}")
        
        # 6. 集群统计
        print("\n📊 6. 集群统计")
        stats = client.get_cluster_stats()
        print(f"\n💡 集群总览:")
        print(f"  🗝️ 总键数: {stats['total_keys']}")
        print(f"  🖥️ 节点数: {stats['nodes']}")
        
        # 7. 清理数据
        print("\n🧹 7. 清理测试数据")
        cleanup_keys = list(test_data.keys()) + [
            "profile:charlie", "tasks", "page_views"
        ]
        
        cleaned = 0
        for key in cleanup_keys:
            try:
                if client.delete(key):
                    cleaned += 1
            except Exception as e:
                print(f"  ⚠️ 清理 {key} 失败: {e}")
        
        print(f"  🗑️ 清理了 {cleaned} 个键")
        
        print("\n🎉 演示完成!")
        print("\n💡 核心特点:")
        print("  ✅ 不计算槽位，让 Redis 自己路由")
        print("  ✅ 简单处理 MOVED/ASK 重定向")
        print("  ✅ 符合 Redis 集群设计理念")
        print("  ✅ 代码简单，逻辑清晰")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        print("\n💡 请确保:")
        print("  1. Redis集群正在运行")
        print("  2. 端口7001-7003可访问")


if __name__ == "__main__":
    if not REDIS_AVAILABLE:
        print("❌ Redis库未安装") 
        print("📦 安装命令: pip install redis")
    else:
        try:
            demo()
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断")
        except Exception as e:
            print(f"\n❌ 程序错误: {e}")