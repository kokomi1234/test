# Redis Cluster Setup Guide

Complete guide for setting up and using Redis cluster with external access.

## Prerequisites

### System Requirements
- Docker 20.10+ 
- Docker Compose 2.0+
- Python 3.7+
- At least 2GB RAM available for Docker

### Port Requirements
The following ports must be available on your system:
- `7001` - Redis node 1 external access
- `7002` - Redis node 2 external access  
- `7003` - Redis node 3 external access

Check port availability:
```bash
netstat -an | grep -E ":(7001|7002|7003)"
```

## Quick Setup

### 1. Clone and Navigate
```bash
git clone <repository>
cd redis-cluster-demo
```

### 2. Start Redis Cluster
```bash
# Make script executable
chmod +x scripts/redis-cluster.sh

# Start cluster
./scripts/redis-cluster.sh start

# Verify cluster is running
./scripts/redis-cluster.sh status
```

### 3. Install Python Dependencies
```bash
# Install basic dependencies
pip install -r requirements.txt

# Or install with development tools
pip install redis redis-py-cluster pytest black flake8
```

### 4. Test Connection
```bash
# Run basic usage example
python examples/basic_usage.py

# Run advanced example
python examples/advanced_usage.py

# Run official client example  
python examples/official_demo.py
```

## Detailed Configuration

### Docker Compose Configuration

The cluster is configured in `docker-compose.yml`:

```yaml
services:
  redis-node-1:
    image: redis:7-alpine
    ports:
      - "7001:6379"
    volumes:
      - "./config/redis-node-1.conf:/usr/local/etc/redis/redis.conf"
      - "./data/node-1:/data"
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - redis-cluster-net

  redis-node-2:
    # Similar configuration...
    
  redis-node-3:
    # Similar configuration...

networks:
  redis-cluster-net:
    driver: bridge
```

### Node Configuration

Each node has its own configuration file in `config/`:

**Key settings:**
```conf
# Enable cluster mode
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000

# Network binding
bind 0.0.0.0
port 6379

# Persistence
appendonly yes
dir /data
```

## Network Architecture

### Internal Communication
```
Docker Network: redis-cluster-net (172.18.0.0/16)

redis-node-1 (172.18.0.2:6379) ←─→ redis-node-2 (172.18.0.3:6379)
        ↑                                    ↓
        └─────────────→ redis-node-3 (172.18.0.4:6379)
```

### External Access
```
Host Network                 Container Network
localhost:7001    ──────→    redis-node-1:6379
localhost:7002    ──────→    redis-node-2:6379  
localhost:7003    ──────→    redis-node-3:6379
```

## Client Connection Patterns

### 1. Single Node Discovery
```python
# Connect to one node, discover others automatically
client = RedisCluster(
    startup_nodes=[{"host": "localhost", "port": 7001}],
    decode_responses=True
)
```

### 2. Multiple Node Discovery  
```python
# Connect to multiple nodes for redundancy
startup_nodes = [
    {"host": "localhost", "port": 7001},
    {"host": "localhost", "port": 7002},
    {"host": "localhost", "port": 7003}
]
client = RedisCluster(startup_nodes=startup_nodes)
```

### 3. DNS-Based (Container Network)
```python
# When running client inside Docker network
startup_nodes = [
    {"host": "redis-node-1", "port": 6379},
    {"host": "redis-node-2", "port": 6379},
    {"host": "redis-node-3", "port": 6379}
]
```

## Slot Distribution

Redis cluster divides the keyspace into 16,384 slots:

```
Node 1: Slots 0-5460     (5,461 slots)
Node 2: Slots 5461-10922 (5,462 slots)  
Node 3: Slots 10923-16383 (5,461 slots)
```

### Key to Slot Mapping
```python
import crc16

def key_to_slot(key):
    """Calculate which slot a key belongs to."""
    return crc16.crc16xmodem(key.encode()) % 16384

# Example:
key_to_slot("user:1001")  # Returns slot number (0-16383)
```

## Data Persistence

### Persistence Strategy
- **RDB Snapshots**: Periodic point-in-time saves
- **AOF Logging**: Append-only file for durability
- **Data Directory**: `./data/node-X/` for each node

### Backup Procedure
```bash
# Stop cluster
./scripts/redis-cluster.sh stop

# Backup data
cp -r data data-backup-$(date +%Y%m%d-%H%M%S)

# Restart cluster
./scripts/redis-cluster.sh start
```

### Recovery Procedure
```bash
# Stop cluster
./scripts/redis-cluster.sh stop

# Restore from backup
rm -rf data
cp -r data-backup-YYYYMMDD-HHMMSS data

# Start cluster
./scripts/redis-cluster.sh start
```

## Performance Tuning

### Connection Pool Settings
```python
from redis.connection import ConnectionPool

pool = ConnectionPool(
    host='localhost',
    port=7001,
    max_connections=20,
    retry_on_timeout=True,
    health_check_interval=30
)
```

### Batch Operations
```python
# Use pipelines for bulk operations
pipe = client.pipeline()
for i in range(1000):
    pipe.set(f"key:{i}", f"value:{i}")
results = pipe.execute()
```

### Hash Tags for Related Data
```python
# Keep related keys on same node
client.set("{user:1001}:profile", profile_data)
client.set("{user:1001}:settings", settings_data) 
client.set("{user:1001}:sessions", session_data)
```

## Monitoring

### Cluster Status
```bash
# Check cluster health
./scripts/redis-cluster.sh status

# View cluster nodes
docker exec redis-node-1 redis-cli cluster nodes

# Check cluster info
docker exec redis-node-1 redis-cli cluster info
```

### Memory Usage
```bash
# Check memory usage per node
for port in 7001 7002 7003; do
    echo "Node $port:"
    docker exec redis-node-$((port-7000)) redis-cli info memory | grep used_memory_human
done
```

### Key Distribution
```bash
# Check key distribution across nodes
for port in 7001 7002 7003; do
    echo "Node $port keys:"
    docker exec redis-node-$((port-7000)) redis-cli dbsize
done
```

## Troubleshooting

### Common Issues

**1. Cluster won't start**
```bash
# Check Docker status
docker ps -a

# Check logs
docker-compose logs

# Reset everything
./scripts/redis-cluster.sh stop
docker system prune -f
rm -rf data/*/nodes.conf
./scripts/redis-cluster.sh start
```

**2. Connection refused**
```bash
# Check if ports are open
telnet localhost 7001

# Check firewall/network
docker exec redis-node-1 redis-cli ping

# Verify cluster network
docker network ls
docker network inspect redis-cluster-demo_redis-cluster-net
```

**3. Slot migration issues**
```bash
# Check cluster state
docker exec redis-node-1 redis-cli cluster nodes

# Fix cluster if needed
docker exec redis-node-1 redis-cli --cluster fix localhost:7001
```

**4. Split brain scenario**
```bash
# Check node connectivity
for port in 7001 7002 7003; do
    docker exec redis-node-$((port-7000)) redis-cli cluster nodes
done

# Reset cluster if corrupted
./scripts/redis-cluster.sh stop
rm -rf data/*/nodes.conf
./scripts/redis-cluster.sh start
```

### Debug Mode

Enable debug logging in client:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Redis cluster client will show detailed logs
client = RedisCluster(...)
```

Enable Redis debug logging:
```bash
# Edit config files to add:
# loglevel debug

# Restart cluster
./scripts/redis-cluster.sh restart
```

## Security Considerations

### Production Checklist
- [ ] Enable authentication (`requirepass`)
- [ ] Configure TLS/SSL encryption
- [ ] Restrict network access (firewall rules)
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement backup encryption

### Authentication Setup
```conf
# In redis-node-X.conf
requirepass your-strong-password
masterauth your-strong-password
```

```python
# In client code
client = RedisCluster(
    startup_nodes=startup_nodes,
    password="your-strong-password"
)
```

## Next Steps

1. **Production Deployment**: Consider Kubernetes, AWS ElastiCache, or Redis Enterprise
2. **Monitoring**: Implement Prometheus + Grafana monitoring
3. **Backup Strategy**: Automated backup to cloud storage
4. **High Availability**: Add replica nodes for each master
5. **Security**: Enable authentication, TLS, and network restrictions

---

For more detailed information, see the [Redis Cluster Tutorial](https://redis.io/topics/cluster-tutorial) in the official Redis documentation.