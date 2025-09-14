# API Reference

Complete API reference for the Redis cluster client libraries in this project.

## SimpleClusterClient

**File**: `src/simple_client.py`

Beginner-friendly Redis cluster client with automatic redirect handling.

### Constructor

```python
SimpleClusterClient(
    hosts=['localhost'],
    ports=[7001, 7002, 7003],
    socket_timeout=5,
    socket_connect_timeout=5,
    decode_responses=True
)
```

**Parameters:**
- `hosts` (list): List of Redis host addresses
- `ports` (list): List of Redis ports to try
- `socket_timeout` (int): Socket timeout in seconds
- `socket_connect_timeout` (int): Connection timeout in seconds  
- `decode_responses` (bool): Automatically decode byte responses to strings

### Methods

#### Basic Operations

##### `set(key, value, ex=None, nx=False)`
Set a key-value pair in the cluster.

**Parameters:**
- `key` (str): Redis key
- `value` (str): Value to store
- `ex` (int, optional): Expiration time in seconds
- `nx` (bool): Only set if key doesn't exist

**Returns:** `bool` - True if successful

**Example:**
```python
client = SimpleClusterClient()
client.set("user:1001", "Alice")
client.set("session:abc", "user_data", ex=3600)  # 1 hour expiry
client.set("counter:new", "1", nx=True)  # Only if doesn't exist
```

##### `get(key)`
Retrieve value by key.

**Parameters:**
- `key` (str): Redis key to retrieve

**Returns:** `str | None` - Value or None if key doesn't exist

**Example:**
```python
value = client.get("user:1001")
if value:
    print(f"User: {value}")
```

##### `delete(key)`
Delete a key from the cluster.

**Parameters:**
- `key` (str): Redis key to delete

**Returns:** `int` - Number of keys deleted (0 or 1)

**Example:**
```python
deleted = client.delete("user:1001")
print(f"Deleted {deleted} keys")
```

##### `exists(key)`
Check if key exists in the cluster.

**Parameters:**
- `key` (str): Redis key to check

**Returns:** `bool` - True if key exists

**Example:**
```python
if client.exists("user:1001"):
    print("User exists")
```

#### Hash Operations

##### `hset(name, key, value)`
Set field in hash.

**Parameters:**
- `name` (str): Hash name
- `key` (str): Field name  
- `value` (str): Field value

**Returns:** `int` - Number of fields added

**Example:**
```python
client.hset("user:1001:profile", "name", "Alice")
client.hset("user:1001:profile", "email", "alice@example.com")
```

##### `hget(name, key)`
Get field from hash.

**Parameters:**
- `name` (str): Hash name
- `key` (str): Field name

**Returns:** `str | None` - Field value or None

**Example:**
```python
name = client.hget("user:1001:profile", "name")
```

##### `hgetall(name)`
Get all fields from hash.

**Parameters:**
- `name` (str): Hash name

**Returns:** `dict` - Dictionary of field-value pairs

**Example:**
```python
profile = client.hgetall("user:1001:profile")
print(f"Profile: {profile}")
```

#### List Operations

##### `lpush(name, *values)`
Push values to left of list.

**Parameters:**
- `name` (str): List name
- `*values`: Values to push

**Returns:** `int` - Length of list after push

**Example:**
```python
client.lpush("notifications:user:1001", "Welcome!", "New message")
```

##### `rpush(name, *values)`
Push values to right of list.

**Parameters:**
- `name` (str): List name  
- `*values`: Values to push

**Returns:** `int` - Length of list after push

##### `lpop(name)`
Pop value from left of list.

**Parameters:**
- `name` (str): List name

**Returns:** `str | None` - Popped value or None if empty

##### `rpop(name)`
Pop value from right of list.

**Parameters:**
- `name` (str): List name

**Returns:** `str | None` - Popped value or None if empty

##### `lrange(name, start, end)`
Get range of list elements.

**Parameters:**
- `name` (str): List name
- `start` (int): Start index (0-based)
- `end` (int): End index (-1 for last element)

**Returns:** `list` - List of values in range

**Example:**
```python
# Get all notifications
all_notifications = client.lrange("notifications:user:1001", 0, -1)

# Get first 10 notifications  
recent = client.lrange("notifications:user:1001", 0, 9)
```

#### Set Operations

##### `sadd(name, *values)`
Add members to set.

**Parameters:**
- `name` (str): Set name
- `*values`: Values to add

**Returns:** `int` - Number of new members added

**Example:**
```python
client.sadd("user:1001:tags", "python", "redis", "developer")
```

##### `srem(name, *values)`
Remove members from set.

**Parameters:**
- `name` (str): Set name
- `*values`: Values to remove

**Returns:** `int` - Number of members removed

##### `smembers(name)`
Get all members of set.

**Parameters:**
- `name` (str): Set name

**Returns:** `set` - Set of all members

**Example:**
```python
tags = client.smembers("user:1001:tags")
print(f"User tags: {tags}")
```

##### `sismember(name, value)`
Check if value is member of set.

**Parameters:**
- `name` (str): Set name
- `value` (str): Value to check

**Returns:** `bool` - True if value is member

#### Utility Methods

##### `ping()`
Test cluster connectivity.

**Returns:** `bool` - True if cluster is responsive

**Example:**
```python
if client.ping():
    print("Cluster is healthy")
```

##### `info(section=None)`
Get Redis server information.

**Parameters:**
- `section` (str, optional): Info section to retrieve

**Returns:** `dict` - Server information

**Example:**
```python
info = client.info("memory")
memory_usage = info.get("used_memory_human")
```

---

## RedirectClusterClient  

**File**: `src/redirect_client.py`

Educational Redis cluster client that demonstrates redirect handling mechanisms.

### Constructor

```python
RedirectClusterClient(
    initial_nodes=[
        ('localhost', 7001),
        ('localhost', 7002), 
        ('localhost', 7003)
    ],
    socket_timeout=5,
    decode_responses=True,
    max_redirects=5
)
```

**Parameters:**
- `initial_nodes` (list): List of (host, port) tuples
- `socket_timeout` (int): Socket timeout in seconds
- `decode_responses` (bool): Decode responses to strings
- `max_redirects` (int): Maximum redirect attempts per command

### Methods

#### Core Operations

##### `execute_command(command, *args, show_redirects=False)`
Execute Redis command with redirect handling.

**Parameters:**
- `command` (str): Redis command name
- `*args`: Command arguments
- `show_redirects` (bool): Print redirect information

**Returns:** `Any` - Command result

**Example:**
```python
client = RedirectClusterClient()

# Basic operations
result = client.execute_command("SET", "key1", "value1")
value = client.execute_command("GET", "key1")

# Show redirect behavior
client.execute_command("SET", "key2", "value2", show_redirects=True)
```

#### Convenience Methods

##### `set(key, value, show_redirects=False)`
Set key with optional redirect display.

**Example:**
```python
client.set("user:1001", "Alice", show_redirects=True)
```

##### `get(key, show_redirects=False)`  
Get key with optional redirect display.

##### `delete(key, show_redirects=False)`
Delete key with optional redirect display.

##### `exists(key, show_redirects=False)`
Check key existence with optional redirect display.

#### Advanced Operations

##### `set_many(data, show_redirects=False)`
Set multiple key-value pairs.

**Parameters:**
- `data` (dict): Dictionary of key-value pairs
- `show_redirects` (bool): Show redirect information

**Example:**
```python
data = {
    "user:1001": "Alice",
    "user:1002": "Bob", 
    "user:1003": "Charlie"
}
client.set_many(data, show_redirects=True)
```

##### `get_many(keys, show_redirects=False)`
Get multiple keys.

**Parameters:**
- `keys` (list): List of keys to retrieve
- `show_redirects` (bool): Show redirect information

**Returns:** `dict` - Dictionary of key-value pairs

##### `cluster_info()`
Get cluster node information.

**Returns:** `dict` - Cluster topology and status

**Example:**
```python
info = client.cluster_info()
print(f"Cluster has {len(info['nodes'])} nodes")
```

#### Statistics and Monitoring

##### `get_redirect_stats()`
Get redirect statistics.

**Returns:** `dict` - Statistics about redirects encountered

**Example:**
```python
stats = client.get_redirect_stats()
print(f"Total redirects: {stats['total_redirects']}")
print(f"Nodes contacted: {stats['nodes_contacted']}")
```

##### `reset_stats()`
Reset redirect statistics.

---

## Error Handling

### Common Exceptions

#### `ConnectionError`
Raised when unable to connect to any cluster node.

```python
try:
    client = SimpleClusterClient()
    client.set("key", "value")
except ConnectionError as e:
    print(f"Cannot connect to cluster: {e}")
```

#### `TimeoutError`
Raised when operation times out.

```python
try:
    value = client.get("key")
except TimeoutError:
    print("Operation timed out")
```

#### `RedisClusterException`
Raised for cluster-specific errors.

```python
try:
    client.execute_command("INVALID_COMMAND")
except RedisClusterException as e:
    print(f"Cluster error: {e}")
```

### Error Recovery

#### Connection Pooling
```python
# Clients automatically retry on different nodes
client = SimpleClusterClient(
    hosts=['localhost'], 
    ports=[7001, 7002, 7003]  # Will try all ports
)
```

#### Timeout Configuration
```python
# Configure appropriate timeouts
client = SimpleClusterClient(
    socket_timeout=10,           # 10 second operation timeout
    socket_connect_timeout=5     # 5 second connection timeout  
)
```

---

## Best Practices

### 1. Key Design

#### Use Hash Tags for Related Data
```python
# Keep user data on same node
client.set("{user:1001}:profile", profile_data)
client.set("{user:1001}:settings", settings_data)
client.set("{user:1001}:sessions", session_data)
```

#### Avoid Hot Keys
```python
# Bad: Single counter key
client.incr("global_counter")

# Good: Distributed counters
import random
shard = random.randint(0, 9)
client.incr(f"counter:shard:{shard}")
```

### 2. Batch Operations

#### Pipeline Operations
```python
# Use pipelines for bulk operations (not implemented in simple client)
# Use official redis-py-cluster for production pipelines

# Alternative: batch operations
data = {"key1": "val1", "key2": "val2", "key3": "val3"}
client.set_many(data)  # RedirectClusterClient only
```

#### Bulk Retrieval
```python
# Batch get operations  
keys = ["user:1001", "user:1002", "user:1003"]
values = client.get_many(keys)  # RedirectClusterClient only
```

### 3. Connection Management

#### Proper Resource Cleanup
```python
class MyApp:
    def __init__(self):
        self.redis = SimpleClusterClient()
    
    def __del__(self):
        # Cleanup connections
        if hasattr(self, 'redis'):
            del self.redis
```

#### Connection Testing
```python
# Test connectivity before critical operations
if not client.ping():
    raise Exception("Redis cluster unavailable")

# Proceed with operations
client.set("important_key", "important_value")
```

### 4. Monitoring Integration

#### Health Checks
```python
def health_check():
    try:
        client = SimpleClusterClient()
        success = client.ping()
        stats = client.info() if hasattr(client, 'info') else {}
        return {
            "healthy": success,
            "memory_usage": stats.get("used_memory_human", "unknown"),
            "connected_clients": stats.get("connected_clients", 0)
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}
```

#### Performance Monitoring
```python
import time

def timed_operation(func, *args, **kwargs):
    start = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"Operation completed in {duration:.3f}s")
        return result
    except Exception as e:
        duration = time.time() - start  
        print(f"Operation failed after {duration:.3f}s: {e}")
        raise

# Usage
timed_operation(client.set, "key", "value")
```

---

## Migration Guide

### From Single Redis to Cluster

#### Key Changes Required
1. **Connection strings**: Use multiple nodes instead of single host
2. **Multi-key operations**: May not work across nodes
3. **Transactions**: Limited to single hash slots
4. **Lua scripts**: Must operate on single hash slot

#### Code Migration
```python
# Before (single Redis)
import redis
r = redis.Redis(host='localhost', port=6379)

# After (cluster)  
from src.simple_client import SimpleClusterClient
r = SimpleClusterClient()
```

### From redis-py to This Library

#### Simple Operations (Compatible)
```python
# Both work the same
r.set("key", "value")
r.get("key")
r.delete("key")
```

#### Advanced Operations (May Differ)
```python  
# redis-py
pipe = r.pipeline()
pipe.set("key1", "val1")
pipe.set("key2", "val2")
pipe.execute()

# This library (RedirectClusterClient)
data = {"key1": "val1", "key2": "val2"}
client.set_many(data)
```

---

For production applications, consider using the official `redis-py-cluster` library which provides more complete functionality and better performance optimizations.