#!/usr/bin/env python3
"""
Advanced Redis Cluster Usage Example

This example demonstrates advanced cluster operations including:
- Redirect handling observation
- Cross-node operations
- Cluster statistics
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from redirect_client import RedirectClusterClient
except ImportError:
    print("❌ Cannot import RedirectClusterClient. Make sure you're running from the project root.")
    sys.exit(1)


def main():
    """Advanced usage demonstration"""
    print("🎯 Redis Cluster - Advanced Usage Example")
    print("=" * 55)
    
    try:
        # Initialize client
        print("\n1. 🔗 Connecting to cluster...")
        client = RedirectClusterClient()
        
        # Advanced operations with redirect observation
        print("\n2. 🔄 Cross-Node Operations with Redirect Handling:")
        
        # Batch operations that will distribute across nodes
        data = {
            "session:user123": "active_session_data",
            "cache:product456": "product_cache_data", 
            "counter:page_views": "1500",
            "config:app_settings": "production_config",
            "temp:user789": "temporary_data"
        }
        
        print("  📝 Setting data across cluster nodes...")
        client.set_many(data)
        
        # Demonstrate cluster statistics
        print("\n3. 📊 Cluster Statistics:")
        stats = client.get_cluster_stats()
        print(f"  🗝️ Total keys: {stats['total_keys']}")
        print(f"  🖥️ Active nodes: {stats['nodes']}")
        print(f"  📈 Key distribution: {stats['distribution']}")
        
        # Hash operations across cluster
        print("\n4. 🗃️ Hash Operations:")
        client.hset("user_profile:alice", "name", "Alice")
        client.hset("user_profile:alice", "email", "alice@example.com")
        client.hset("user_profile:alice", "role", "admin")
        
        profile = client.hgetall("user_profile:alice")
        print(f"  👤 User profile: {profile}")
        
        # List operations
        print("\n5. 📋 List Operations:")
        client.rpush("task_queue", "process_orders", "send_emails", "cleanup_logs")
        queue_length = client.llen("task_queue")
        print(f"  📝 Task queue length: {queue_length}")
        
        next_task = client.lpop("task_queue")
        print(f"  ✅ Next task: {next_task}")
        
        # Set operations
        print("\n6. 🎯 Set Operations:")
        client.sadd("online_users", "alice", "bob", "charlie")
        online_count = client.scard("online_users")
        print(f"  👥 Online users: {online_count}")
        
        online_users = client.smembers("online_users")
        print(f"  📋 User list: {sorted(online_users)}")
        
        # Cleanup
        print("\n7. 🧹 Cleaning up...")
        cleanup_keys = list(data.keys()) + [
            "user_profile:alice", "task_queue", "online_users"
        ]
        
        cleaned = 0
        for key in cleanup_keys:
            try:
                if client.delete(key):
                    cleaned += 1
            except Exception as e:
                print(f"  ⚠️ Failed to clean {key}: {e}")
        
        print(f"  🗑️ Cleaned {cleaned} keys")
        
        print("\n🎉 Advanced usage example completed!")
        print("\n💡 Key learnings:")
        print("  ✅ Observed Redis cluster redirect behavior")
        print("  ✅ Demonstrated cross-node data distribution")
        print("  ✅ Used various Redis data structures")
        print("  ✅ Monitored cluster statistics")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure:")
        print("  1. Redis cluster is running: ./scripts/redis-cluster.sh start")
        print("  2. Dependencies installed: pip install -r requirements.txt")


if __name__ == "__main__":
    main()