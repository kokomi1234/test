#!/usr/bin/env python3
"""
Redis Official Library Demo - Cluster Aware

This example demonstrates using redis-py (official Redis library) 
with manual cluster handling for Docker environments.

The redis.cluster.RedisCluster has issues with Docker container names,
so this shows practical workarounds for production use.
"""

import redis
import time
from typing import Dict, List, Optional

class ClusterAwareRedisClient:
    """
    A wrapper around regular Redis clients that handles cluster redirects.
    This approach works well in Docker environments where RedisCluster 
    auto-discovery fails due to container name resolution.
    """
    
    def __init__(self, nodes: List[tuple]):
        """
        Initialize connections to all cluster nodes.
        
        Args:
            nodes: List of (host, port) tuples for cluster nodes
        """
        self.nodes = nodes
        self.connections = {}
        self.redirect_map = {
            "redis-node-1:6379": 7001,
            "redis-node-2:6379": 7002, 
            "redis-node-3:6379": 7003
        }
        
        # Establish connections to all nodes
        for host, port in nodes:
            try:
                conn = redis.Redis(
                    host=host, 
                    port=port, 
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                conn.ping()  # Test connection
                self.connections[f"{host}:{port}"] = conn
                print(f"✅ Connected to Redis node {host}:{port}")
            except Exception as e:
                print(f"❌ Failed to connect to {host}:{port}: {e}")
        
        if not self.connections:
            raise Exception("❌ No Redis nodes available")
        
        self.primary = next(iter(self.connections.values()))
    
    def execute_with_redirect(self, operation: str, *args, **kwargs):
        """
        Execute Redis operation with automatic redirect handling.
        
        Args:
            operation: Redis command name (e.g., 'set', 'get', 'hset')
            *args, **kwargs: Command arguments
        """
        last_error = None
        
        # Try each connection once
        for node_name, conn in self.connections.items():
            try:
                method = getattr(conn, operation)
                result = method(*args, **kwargs)
                return result
            except redis.exceptions.ResponseError as e:
                error_msg = str(e)
                if "MOVED" in error_msg:
                    # Parse redirect: "MOVED 1234 redis-node-2:6379" or just "1234 redis-node-2:6379"
                    parts = error_msg.split()
                    target_node = None
                    
                    # Find the target node in the error message
                    for part in parts:
                        if "redis-node-" in part and ":6379" in part:
                            target_node = part
                            break
                    
                    if target_node and target_node in self.redirect_map:
                        target_port = self.redirect_map[target_node]
                        target_key = f"localhost:{target_port}"
                        if target_key in self.connections:
                            try:
                                target_conn = self.connections[target_key]
                                target_method = getattr(target_conn, operation)
                                result = target_method(*args, **kwargs)
                                print(f"🔄 Redirected {operation} to {target_key}")
                                return result
                            except Exception as redirect_error:
                                print(f"❌ Redirect to {target_key} failed: {redirect_error}")
                                last_error = redirect_error
                                continue
                last_error = e
            except Exception as e:
                last_error = e
                continue
        
        # If we get here, all attempts failed
        raise Exception(f"❌ Failed to execute {operation}: {last_error}")
    
    def set(self, key: str, value: str) -> bool:
        """Set a key-value pair with cluster redirect handling."""
        return self.execute_with_redirect('set', key, value)
    
    def get(self, key: str) -> Optional[str]:
        """Get a value with cluster redirect handling."""
        return self.execute_with_redirect('get', key)
    
    def hset(self, name: str, mapping: Dict) -> int:
        """Set hash fields with cluster redirect handling."""
        return self.execute_with_redirect('hset', name, mapping=mapping)
    
    def hgetall(self, name: str) -> Dict:
        """Get all hash fields with cluster redirect handling."""
        return self.execute_with_redirect('hgetall', name)
    
    def delete(self, *keys) -> int:
        """Delete keys with cluster redirect handling (one by one for cross-slot compatibility)."""
        total_deleted = 0
        for key in keys:
            try:
                deleted = self.execute_with_redirect('delete', key)
                total_deleted += deleted
            except Exception as e:
                print(f"   Failed to delete {key}: {e}")
        return total_deleted
    
    def exists(self, *keys) -> int:
        """Check key existence with cluster redirect handling."""
        return self.execute_with_redirect('exists', *keys)
    
    def ping_all_nodes(self) -> Dict[str, bool]:
        """Ping all cluster nodes to check connectivity."""
        results = {}
        for node_name, conn in self.connections.items():
            try:
                conn.ping()
                results[node_name] = True
            except Exception:
                results[node_name] = False
        return results
    
    def get_cluster_info(self) -> Dict:
        """Get cluster information from first available node."""
        for conn in self.connections.values():
            try:
                info = conn.info()
                return {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "redis_version": info.get("redis_version", "unknown"),
                    "nodes": len(self.connections)
                }
            except Exception as e:
                continue
        return {"error": "Could not get cluster info"}


def main():
    """Main demonstration function."""
    print("🎯 Redis Official Library Demo (Cluster Aware)")
    print("=" * 60)
    
    # Initialize cluster-aware client
    nodes = [
        ("localhost", 7001),
        ("localhost", 7002),
        ("localhost", 7003)
    ]
    
    try:
        client = ClusterAwareRedisClient(nodes)
        print(f"✅ Cluster client initialized with {len(client.connections)} nodes\n")
    except Exception as e:
        print(f"❌ Failed to initialize cluster client: {e}")
        print("\n💡 Make sure Redis cluster is running:")
        print("   ./scripts/redis-cluster.sh start")
        return
    
    # 1. Basic Operations
    print("📝 1. Basic Key-Value Operations")
    print("-" * 40)
    
    # Set some data
    test_data = {
        "user:alice": "Alice Johnson",
        "user:bob": "Bob Smith", 
        "product:laptop": "MacBook Pro",
        "session:abc123": "active_session"
    }
    
    for key, value in test_data.items():
        success = client.set(key, value)
        print(f"   Set {key}: {'✅' if success else '❌'}")
    
    # Retrieve data
    print("\n📖 Retrieving data:")
    for key in test_data.keys():
        value = client.get(key)
        print(f"   {key} = {value}")
    
    # 2. Hash Operations
    print(f"\n🏠 2. Hash Operations")
    print("-" * 40)
    
    user_profile = {
        "name": "Charlie Brown",
        "email": "charlie@example.com", 
        "age": "28",
        "city": "San Francisco"
    }
    
    client.hset("user:charlie:profile", user_profile)
    retrieved_profile = client.hgetall("user:charlie:profile")
    print(f"   User profile: {retrieved_profile}")
    
    # 3. Cluster Health Check
    print(f"\n🩺 3. Cluster Health Check")
    print("-" * 40)
    
    ping_results = client.ping_all_nodes()
    for node, status in ping_results.items():
        print(f"   {node}: {'🟢 Online' if status else '🔴 Offline'}")
    
    cluster_info = client.get_cluster_info()
    if "error" not in cluster_info:
        print(f"\n📊 Cluster Information:")
        for key, value in cluster_info.items():
            print(f"   {key}: {value}")
    
    # 4. Performance Test
    print(f"\n⚡ 4. Performance Test")
    print("-" * 40)
    
    start_time = time.time()
    operations = 100
    
    for i in range(operations):
        client.set(f"perf_test:{i}", f"value_{i}")
    
    for i in range(operations):
        client.get(f"perf_test:{i}")
    
    end_time = time.time()
    duration = end_time - start_time
    ops_per_second = (operations * 2) / duration  # 2 ops per iteration (set + get)
    
    print(f"   Completed {operations * 2} operations in {duration:.2f}s")
    print(f"   Performance: {ops_per_second:.1f} ops/sec")
    
    # 5. Cleanup
    print(f"\n🧹 5. Cleanup")
    print("-" * 40)
    
    cleanup_keys = list(test_data.keys()) + ["user:charlie:profile"] + [f"perf_test:{i}" for i in range(operations)]
    deleted = client.delete(*cleanup_keys)
    print(f"   Deleted {deleted} keys")
    
    print("\n✅ Demo completed successfully!")
    print("\n💡 This approach works well in Docker environments where")
    print("   RedisCluster auto-discovery fails due to container names.")


if __name__ == "__main__":
    print("Starting Redis Official Library Demo...")
    print("Make sure your Redis cluster is running: ./scripts/redis-cluster.sh start\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Redis cluster is running")
        print("2. Check if ports 7001-7003 are accessible") 
        print("3. Verify redis library is installed: pip install redis")