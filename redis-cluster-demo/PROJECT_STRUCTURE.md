# 📁 Redis Cluster Demo - Project Structure

Professional project organization for Redis cluster demonstration and learning.

## 🏗️ Directory Layout

```
redis-cluster-demo/
├── 📄 README_NEW.md          # ✨ New comprehensive documentation  
├── 📄 requirements.txt       # Python dependencies (updated)
├── 🐳 docker-compose.yml     # Redis cluster configuration
├── 📄 PROJECT_STRUCTURE.md   # This organization guide
│
├── 📁 src/                   # 🎯 Source code directory
│   ├── simple_client.py      # SimpleClusterClient (beginner-friendly)
│   └── redirect_client.py    # RedirectClusterClient (educational)
│
├── 📁 config/                # ⚙️ Configuration files
│   ├── redis-node-1.conf     # Node 1 configuration
│   ├── redis-node-2.conf     # Node 2 configuration  
│   └── redis-node-3.conf     # Node 3 configuration
│
├── 📁 scripts/               # 🛠️ Management scripts
│   ├── redis-cluster.sh      # Main cluster operations
│   └── install_deps.sh       # Dependency installation
│
├── 📁 examples/              # 📚 Usage demonstrations
│   ├── basic_usage.py        # Simple operations (SimpleClusterClient)
│   ├── advanced_usage.py     # Advanced features (RedirectClusterClient)
│   └── redis_official_demo.py # Production client (redis>=4.0.0)
│
├── 📁 docs/                  # 📖 Documentation hub
│   ├── SETUP_GUIDE.md        # Complete setup guide
│   └── API_REFERENCE.md      # Full API documentation
│
└── 📁 data/                  # 💾 Persistent data (auto-created)
    ├── node-1/               # Node 1 data and logs
    ├── node-2/               # Node 2 data and logs
    └── node-3/               # Node 3 data and logs
```

## 🎯 Component Status & Purpose

### 🏠 Root Files
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `README_NEW.md` | Comprehensive project guide | ✅ **New** | Professional documentation |
| `requirements.txt` | Updated Python dependencies | ✅ **Updated** | Includes redis-py-cluster |
| `docker-compose.yml` | 3-node cluster config | ✅ **Updated** | Fixed config/ paths |
| `PROJECT_STRUCTURE.md` | This organization guide | ✅ **New** | Professional structure |

### 💻 Source Libraries (`src/`)
| Library | Class Name | Target User | Key Features |
|---------|------------|-------------|--------------|
| `simple_client.py` | `SimpleClusterClient` | 🎓 **Beginners** | Easy CRUD, auto-redirects |
| `redirect_client.py` | `RedirectClusterClient` | 📚 **Learners** | Educational redirects, stats |

### ⚙️ Configuration (`config/`)  
| Config File | Redis Node | External Port | Internal Communication |
|-------------|------------|---------------|----------------------|
| `redis-node-1.conf` | redis-node-1 | `localhost:7001` | `redis-node-1:6379` |
| `redis-node-2.conf` | redis-node-2 | `localhost:7002` | `redis-node-2:6379` |
| `redis-node-3.conf` | redis-node-3 | `localhost:7003` | `redis-node-3:6379` |

### 🛠️ Management Scripts (`scripts/`)
| Script | Available Commands | Purpose |
|--------|-------------------|---------|
| `redis-cluster.sh` | `start`, `stop`, `status`, `restart`, `test` | Complete cluster lifecycle |
| `install_deps.sh` | - | Automated environment setup |

### 📚 Examples & Demos (`examples/`)
| Example | Client Library | Demonstrates | Difficulty |
|---------|---------------|-------------|------------|
| `basic_usage.py` | SimpleClusterClient | CRUD operations | 🟢 **Easy** |
| `advanced_usage.py` | RedirectClusterClient | Redirect mechanics | 🟡 **Medium** |
| `redis_official_demo.py` | redis>=4.0.0 | Production patterns | 🟠 **Advanced** |

### 📖 Documentation (`docs/`)
| Document | Content | Audience | Completeness |
|----------|---------|----------|--------------|
| `SETUP_GUIDE.md` | Complete setup & troubleshooting | 🔧 **Operators** | ✅ **Complete** |
| `API_REFERENCE.md` | Full API docs & examples | 👨‍💻 **Developers** | ✅ **Complete** |

## 🚀 Usage Workflows

### 🎯 Quick Start (New Users)
```bash
# 1. Start Redis cluster
./scripts/redis-cluster.sh start

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run basic example  
python examples/basic_usage.py

# 4. Read documentation
cat README_NEW.md
```

### 👨‍💻 Development (Programmers)
```python
# Standard import pattern
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import appropriate client
from simple_client import SimpleClusterClient       # For simple apps
from redirect_client import RedirectClusterClient   # For learning

# Use in application
client = SimpleClusterClient()
client.set("user:1001", "Alice")
```

### 🎓 Learning (Students & Educators)
```bash
# Educational workflow
./scripts/redis-cluster.sh start                    # Start cluster
python examples/advanced_usage.py                   # See redirects in action
python examples/redis_official_demo.py              # Production patterns

# Study documentation
open docs/SETUP_GUIDE.md                           # Technical details
open docs/API_REFERENCE.md                         # API examples
```

### 🏢 Production (Engineers)
```python
# Production-ready approach
from rediscluster import RedisCluster

# Robust connection
startup_nodes = [{"host": "localhost", "port": 7001}]
client = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

# Enterprise features
client.set("key", "value")
# Built-in: connection pooling, failover, monitoring
```

## 🏗️ Architecture Principles

### 📂 Separation of Concerns
```
src/        → Core library code (reusable)
config/     → Redis configurations (deployment)  
scripts/    → Operational tools (management)
examples/   → Usage demonstrations (learning)
docs/       → Documentation (reference)
data/       → Runtime persistence (auto-managed)
```

### 🎯 Clear Naming Conventions
- **Files**: Descriptive, purpose-clear names
- **Classes**: `*ClusterClient` pattern for consistency  
- **Scripts**: Action-oriented names (`redis-cluster.sh`)
- **Configs**: Node-specific naming (`redis-node-X.conf`)

### 🔌 Import Strategy
```python
# From examples/ directory:
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Clean, explicit imports:
from simple_client import SimpleClusterClient      # Beginner-friendly
from redirect_client import RedirectClusterClient  # Educational
```

## 📊 Professional Benefits

### ✅ Before vs After Comparison

| Aspect | **Before** (Flat Structure) | **After** (Organized) |
|--------|------------------------------|----------------------|
| **File Organization** | All files in root directory | Logical directory hierarchy |
| **Documentation** | Single README, scattered info | Comprehensive docs/ directory |
| **Code Structure** | Mixed purposes in same files | Clean separation (src/) |
| **Examples** | Embedded in source code | Dedicated examples/ directory |
| **Configuration** | Inline in docker-compose | Separate config/ files |
| **Maintainability** | Difficult to navigate | Professional structure |
| **Onboarding** | Overwhelming for new users | Clear learning path |

### 🎯 Industry Standards Compliance
- ✅ **Standard Layout**: `src/`, `docs/`, `examples/` structure
- ✅ **Clear Dependencies**: Explicit `requirements.txt`
- ✅ **Comprehensive Docs**: Setup, API, structure guides
- ✅ **Multiple User Paths**: Beginner → Advanced → Production
- ✅ **Easy Maintenance**: Logical file organization
- ✅ **Professional Naming**: Consistent, descriptive conventions

## 🔄 Development Guidelines

### Adding New Components

#### New Client Library
```bash
# Add to source
touch src/new_client.py

# Create corresponding example
touch examples/new_client_demo.py

# Update documentation
echo "## NewClient" >> docs/API_REFERENCE.md
```

#### New Configuration
```bash
# Add config file
touch config/redis-new-feature.conf

# Update docker-compose if needed
vim docker-compose.yml

# Document in setup guide
echo "### New Feature Setup" >> docs/SETUP_GUIDE.md
```

#### New Documentation
```bash
# Add to docs directory
touch docs/NEW_GUIDE.md

# Link from main README
echo "[New Guide](docs/NEW_GUIDE.md)" >> README_NEW.md
```

### Import Path Management
```python
# Standard pattern for all examples/
import sys
import os

# Reliable project root detection
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Then import
from simple_client import SimpleClusterClient
```

### Documentation Maintenance
- **README_NEW.md**: User-facing changes, new features
- **API_REFERENCE.md**: New methods, classes, examples  
- **SETUP_GUIDE.md**: Configuration changes, troubleshooting
- **PROJECT_STRUCTURE.md**: Structural changes, new directories

## 🎉 Next Steps

### For Users
1. **Start Here**: Read `README_NEW.md` for quick start
2. **Learn**: Run examples in order (basic → advanced → official)
3. **Deep Dive**: Study `docs/SETUP_GUIDE.md` for technical details
4. **Reference**: Use `docs/API_REFERENCE.md` for development

### For Contributors
1. **Understand Structure**: This document (`PROJECT_STRUCTURE.md`)
2. **Follow Conventions**: Use established naming and organization
3. **Add Documentation**: Update relevant docs for changes
4. **Test Examples**: Ensure all examples work with changes

### For Educators
1. **Teaching Path**: `examples/basic_usage.py` → `examples/advanced_usage.py`
2. **Technical Details**: `docs/SETUP_GUIDE.md` for deep understanding
3. **Production Readiness**: `examples/redis_official_demo.py` for real applications

---

This professional structure transforms the Redis cluster demo from a simple script collection into a comprehensive, maintainable, and educational project suitable for learning, development, and production reference.