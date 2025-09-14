# Redis Cluster External Access

A production-ready Redis cluster setup with external client access capabilities, educational examples, and comprehensive documentation.

## ✨ Features

- 🚀 **One-command cluster setup** with Docker Compose
- 🔗 **External client access** via port mapping (7001-7003)
- 🎓 **Educational examples** for understanding cluster mechanics
- 📚 **Multiple client implementations** (simple, advanced, official)
- ⚡ **DNS service discovery** for optimal performance
- 📊 **Monitoring and management** scripts

## 🏗️ Architecture

```
External Access Layer:
  localhost:7001 ─┐
  localhost:7002 ─┼─► Redis Cluster (3 nodes)
  localhost:7003 ─┘

Internal Network (redis-cluster-net):
  redis-node-1:6379 ←─► redis-node-2:6379
         ↕                    ↕
  redis-node-3:6379 ←─────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.7+
- pip

### 1. Start the Cluster
```bash
# Start Redis cluster
./scripts/redis-cluster.sh start

# Verify cluster status  
./scripts/redis-cluster.sh status
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Examples
```bash
# Basic usage (beginner-friendly)
python examples/basic_usage.py

# Advanced usage (redirect handling)
python examples/advanced_usage.py

# Official redis-py library example (production-ready)
python examples/redis_official_demo.py
```

## 📚 Client Libraries

### 🌟 For Beginners
```python
from src.simple_client import SimpleClusterClient

client = SimpleClusterClient()
client.set("user:1", "Alice")
user = client.get("user:1")
```

### 🎓 For Learning Cluster Mechanics
```python
from src.redirect_client import RedirectClusterClient

client = RedirectClusterClient()
# Observe Redis cluster redirects in action
client.set_many({"key1": "val1", "key2": "val2"})
```

### 🏆 For Production (Recommended)
```python
from redis.cluster import RedisCluster

# Modern redis-py (>=4.0.0) with built-in cluster support
rc = RedisCluster(host="localhost", port=7001, decode_responses=True)
rc.set("key", "value")
```

## 📁 Project Structure

```
redis-cluster-demo/
├── 📄 README.md              # This file
├── 📄 requirements.txt       # Python dependencies
├── 🐳 docker-compose.yml     # Cluster configuration
│
├── 📁 src/                   # Client libraries
│   ├── simple_client.py      # Beginner-friendly client
│   └── redirect_client.py    # Educational redirect client
│
├── 📁 config/                # Redis configurations
│   ├── redis-node-1.conf     # Node 1 config
│   ├── redis-node-2.conf     # Node 2 config
│   └── redis-node-3.conf     # Node 3 config
│
├── 📁 scripts/               # Management scripts
│   ├── redis-cluster.sh      # Main cluster management
│   └── install_deps.sh       # Dependency installation
│
├── 📁 examples/              # Usage examples
│   ├── basic_usage.py        # Simple CRUD operations
│   ├── advanced_usage.py     # Complex cluster operations
│   └── redis_official_demo.py # Production-ready redis-py example
│
├── 📁 docs/                  # Documentation
└── 📁 data/                  # Persistent data (auto-created)
```

## 🎯 Usage Scenarios

| Scenario | Recommended Client | Why? |
|----------|-------------------|------|
| 🏢 **Production Apps** | `ClusterAwareRedisClient` | Production-ready, Docker-compatible |
| 🎓 **Learning Redis** | `SimpleClusterClient` | See redirect handling in action |
| 🔍 **Debugging Issues** | `RedirectClusterClient` | Observe cluster behavior |
| 📚 **Teaching/Demos** | Both custom clients | Show how Redis cluster works |

## ⚙️ Configuration

### Cluster Settings
- **Nodes**: 3 (redis-node-1, redis-node-2, redis-node-3)
- **External Ports**: 7001, 7002, 7003
- **Internal Communication**: DNS service discovery
- **Data Persistence**: `./data/` directory

### Network Architecture
- **Docker Network**: `redis-cluster-net` (bridge)
- **Node Discovery**: Container names (DNS)
- **External Access**: Port mapping to localhost

## 🛠️ Management Commands

```bash
# Cluster management
./scripts/redis-cluster.sh start          # Start cluster
./scripts/redis-cluster.sh stop           # Stop cluster  
./scripts/redis-cluster.sh restart        # Restart (clean)
./scripts/redis-cluster.sh status         # Check status
./scripts/redis-cluster.sh test           # Run tests

# Development
pip install -r requirements.txt           # Install deps
python examples/basic_usage.py            # Test basic ops
python examples/advanced_usage.py         # Test advanced ops
```

## 🔧 Technical Deep Dive

### Redis Cluster Redirect Handling

Redis cluster uses **MOVED** redirects to route commands to the correct node:

```python
# What happens internally:
1. Client sends command to any node
2. Node returns: "MOVED 12345 redis-node-2:6379"  
3. Client parses redirect and retries on correct node
4. Command executes successfully
```

### Key Discovery
- **Slot Calculation**: Each key maps to one of 16,384 slots
- **Node Mapping**: Slots are distributed across cluster nodes
- **Redirect Handling**: Clients follow MOVED/ASK redirects

### External Access Design
```
Container Network (Internal):
  redis-node-1:6379 ←─► redis-node-2:6379 ←─► redis-node-3:6379

Host Network (External):
  localhost:7001    ←─► localhost:7002    ←─► localhost:7003
      ↓                      ↓                      ↓
  redis-node-1:6379    redis-node-2:6379    redis-node-3:6379
```

## 🚨 Troubleshooting

### Common Issues

**Cluster won't start**
```bash
# Check Docker status
docker ps

# Check logs
docker-compose logs redis-node-1

# Reset everything
./scripts/redis-cluster.sh stop
docker system prune -f
./scripts/redis-cluster.sh start
```

**Connection refused**
```bash
# Check port availability
netstat -an | grep 700[1-3]

# Verify cluster status
./scripts/redis-cluster.sh status
```

**Import errors in examples**
```bash
# Install dependencies
pip install -r requirements.txt

# Run from project root
cd redis-cluster-demo
python examples/basic_usage.py
```

## 📈 Performance Tips

1. **Use connection pooling** for production applications
2. **Batch operations** when possible to reduce round trips
3. **Monitor redirect patterns** to optimize key distribution
4. **Use hash tags** `{tag}:key` for related keys in same slot
5. **Configure appropriate timeout values** for your network

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Redis team for the excellent clustering implementation
- Docker team for making deployment so simple
- Python redis-py contributors for the client libraries

---

**Need help?** Check the [docs/](docs/) directory for detailed guides, or open an issue!