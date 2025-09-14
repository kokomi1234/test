#!/usr/bin/env python3
"""
Basic Redis Cluster Usage Example

This example demonstrates basic CRUD operations using Redis cluster clients.
Perfect for beginners to understand cluster operations.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from simple_client import SimpleClusterClient
except ImportError:
    print("❌ Cannot import SimpleClusterClient. Make sure you're running from the project root.")
    sys.exit(1)


def main():
    """Basic usage demonstration"""
    print("🎯 Redis Cluster - Basic Usage Example")
    print("=" * 50)
    
    try:
        # Initialize client
        print("\n1. 🔗 Connecting to cluster...")
        client = SimpleClusterClient()
        
        # Basic CRUD operations
        print("\n2. 📝 Basic CRUD Operations:")
        
        # Create
        client.set("user:1001", "Alice Johnson")
        client.set("user:1002", "Bob Smith")
        print("  ✅ Data created")
        
        # Read
        alice = client.get("user:1001")
        bob = client.get("user:1002")
        print(f"  📖 Read: Alice = {alice}")
        print(f"  📖 Read: Bob = {bob}")
        
        # Update
        client.set("user:1001", "Alice Johnson-Smith")
        updated_alice = client.get("user:1001")
        print(f"  🔄 Updated: Alice = {updated_alice}")
        
        # Delete
        deleted = client.delete("user:1002")
        print(f"  🗑️ Deleted: {deleted} record(s)")
        
        # Verify deletion
        bob_after_delete = client.get("user:1002")
        print(f"  ✅ Verified: Bob after delete = {bob_after_delete}")
        
        # Cleanup
        client.delete("user:1001")
        print("\n3. 🧹 Cleanup completed")
        
        print("\n🎉 Basic usage example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure:")
        print("  1. Redis cluster is running: ./scripts/redis-cluster.sh start")
        print("  2. Dependencies installed: pip install -r requirements.txt")


if __name__ == "__main__":
    main()