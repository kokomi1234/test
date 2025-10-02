# Node.js 高并发订单系统演示 (Node.js High-Concurrency Order System Demo)

![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white) ![Express.js](https://img.shields.io/badge/Express.js-000000?style=for-the-badge&logo=express&logoColor=white) ![Vue.js](https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D) ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white) ![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

这是一个迷你的、但功能完备的全栈订单系统。它通过 Vue.js 前端和 Node.js 后端，并整合了 MySQL、Redis Cluster 和 Kafka，专门用于演示如何通过异步架构解决高并发场景下的“超卖”问题。

## ✨ 功能特性 (Features)

- **全栈体验**: 包含可交互的 Vue.js 前端界面和高性能的 Node.js 后端服务。
- **商品管理**: 提供完整的商品增、删、查 API。
- **异步下单**: 用户在前端下单，请求会立即得到响应，订单在后台通过消息队列异步处理，极大提升用户体验。
- **高并发安全**: 采用 Redis 原子操作进行库存预扣减，从根本上防止了竞态条件下的超卖问题。
- **缓存加速**: 使用 Redis 缓存商品详情，降低数据库读取压力，提升查询性能。
- **服务解耦**: API 服务和订单处理服务通过 Kafka 解耦，提高了系统的健壮性和可扩展性。
- **一键启动**: 所有依赖的基础设施（数据库、缓存、消息队列）都已容器化，可通过 Docker Compose 一键启动。

## 🛠️ 技术栈 (Tech Stack)

- **前端**: Vue.js, Vite, Axios
- **后端**: Node.js, Express.js
- **数据库**: MySQL
- **缓存**: Redis (Cluster Mode)
- **消息队列**: Apache Kafka
- **运行时/工具**: Docker, Docker Compose, `concurrently`
- **Node.js 库**: `express`, `mysql2`, `redis`, `kafkajs`, `dotenv`

## 📂 项目结构 (Project Structure)

```
.
├── my-frontend-app/      # Vue.js 前端应用
│   ├── src/
│   │   ├── components/   # Vue 组件
│   │   ├── App.jsx       # 主应用组件
│   │   └── ...
│   ├── index.html
│   ├── package.json
│   └── vite.config.js    # Vite 配置文件 (含代理)
├── docker-compose.yml    # Docker编排文件，定义并管理所有基础设施服务
├── .env.example          # 环境变量示例文件
├── index.js              # API 服务器主入口，处理HTTP请求
├── order-consumer.js     # Kafka 消费者，在后台处理订单
├── db.js                 # MySQL 数据库连接配置
├── redisClient.js        # Redis 集群客户端配置
├── kafka.js              # Kafka 生产者和消费者实例配置
├── sync-stock.js         # 工具脚本：将MySQL库存同步到Redis
├── init.sql              # 数据库初始化脚本
├── package.json          # 后端项目依赖和脚本定义
└── API_DOCUMENTATION.md  # API 接口文档
```

## 🚀 安装与启动 (Installation and Setup)

请确保你的本地环境已经安装了 [Docker](https://www.docker.com/) 和 [Docker Compose](https://docs.docker.com/compose/install/)。

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd node-order-system
```

### 2. 配置环境变量

复制示例环境变量文件，创建一个你自己的 `.env` 文件。

```bash
cp .env.example .env
```

通常情况下，你**无需修改** `.env` 文件中的内容，因为所有服务都将在 Docker 网络中运行，并使用默认配置。

### 3. 启动所有后端服务

在项目根目录下，运行以下命令来启动所有服务，包括 MySQL, Redis Cluster, Kafka 和 Zookeeper。

```bash
docker-compose up -d
```

这个过程可能需要几分钟，因为它会下载所有服务的 Docker 镜像。`redis-cluster-creator` 服务会自动配置 Redis 集群，你可以在日志中看到它的执行过程。

### 4. 安装后端 Node.js 依赖

```bash
npm install
```

### 5. 同步初始库存到 Redis

在首次启动或数据库商品信息有变动后，你需要运行此脚本将 MySQL 中的库存数据同步到 Redis。这是保证系统正常运行的关键一步。

```bash
npm run sync:stock
```

### 6. 运行后端项目

使用以下命令同时启动 API 服务器和 Kafka 消费者。

```bash
npm start
```

现在，后端服务已经成功运行！
- API 服务器运行在 `http://localhost:3000`
- Kafka 消费者正在后台监听订单消息

### 7. 启动前端应用

在**新的终端窗口**中，进入前端应用目录，安装依赖并启动开发服务器。

```bash
# 进入前端项目目录
cd my-frontend-app

# 安装依赖
npm install

# 启动 Vite 开发服务器
npm run dev
```

前端应用现在运行在 `http://localhost:5173` (或终端提示的其他端口)。打开浏览器访问此地址即可看到应用界面。

## 📝 使用示例 (Usage)

启动所有服务后，直接在浏览器中打开前端应用地址 (`http://localhost:5173`) 即可与系统交互。你也可以使用 `curl` 或 Postman 等工具直接与后端 API 交互。

**1. 创建一个新商品**
```bash
curl -X POST http://localhost:3000/products \
-H "Content-Type: application/json" \
-d '{
  "name": "无线耳机",
  "stock": 100,
  "imageUrl": "http://example.com/headphone.jpg"
}'
```

**2. 下一个订单**
假设你创建的商品 ID 为 `1`，库存为 `100`。

```bash
curl -X POST http://localhost:3000/orders \
-H "Content-Type: application/json" \
-d '{
  "productId": 1,
  "quantity": 2
}'
```
你会立即收到 `{"message":"订单请求已接受，正在处理中"}` 的响应。

同时，在运行 `npm start` 的终端中，你会看到类似以下的日志流：
1.  **API 服务器**: `[API] 库存预扣减成功，订单请求已发送到 Kafka...`
2.  **消费者**: `[Consumer] 收到已预留库存的订单消息...`
3.  **消费者**: `[Consumer] 订单处理成功: ... SQL 库存已同步。`

**3. 模拟库存不足**
如果尝试购买一个库存不足的商品（例如，库存只有1个，但你想买2个），你会立即收到失败响应：
```json
{ "error": "库存不足" }
```