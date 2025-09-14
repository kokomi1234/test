# Redis Sentinel 高可用集群 Docker 部署指南

本项目通过 Docker Compose 搭建了一个包含一个主节点（Master）、两个从节点（Slave）和三个哨兵（Sentinel）的 Redis 高可用集群。项目包含了完整的配置文件、演示代码以及一份详细的问题排查记录。

## 1. 如何运行

请严格按照以下步骤操作，以确保环境正确设置。

### 前提

*   已安装 Docker 和 Docker Compose。
*   已安装 Python 3 和 pip。

### 步骤 1：启动 Redis 集群

在项目根目录运行以下命令，启动所有 Docker 服务。

```bash
docker-compose up -d
```

### 步骤 2：配置主机 DNS 解析

这是**在本地电脑上**运行客户端代码（如 Python 脚本）的关键一步。

1.  打开 `/etc/hosts` 文件（需要管理员权限）：
    ```bash
    sudo nano /etc/hosts
    ```
2.  在文件末尾添加以下一行，将 Docker 服务名 `redis-master` 指向 `localhost`：
    ```
    127.0.0.1 redis-master
    ```
3.  保存并关闭文件。此更改会立即生效，无需重启或 `source`。

### 步骤 3：安装 Python 依赖

```bash
pip install redis
```

### 步骤 4：运行演示脚本

*   **测试主从连接和读写分离：**
    ```bash
    python client_demo.py
    ```
*   **测试分布式锁：**
    为了观察锁竞争，请打开两个终端，分别运行以下命令：
    ```bash
    # 终端 1
    python locking_demo.py

    # 终端 2
    python locking_demo.py
    ```

---

## 2. 问题排查之旅（总结）

在搭建过程中，我们遇到了三个核心问题，以下是它们的症状、根源和最终解决方案。

### 问题 1：Sentinel 容器启动失败

*   **症状**：Sentinel 容器启动后立即退出，日志显示 `Can't resolve instance hostname`。
*   **根源**：Redis Sentinel 的特殊设计，它默认不会主动解析配置文件中 `monitor` 指令后的主机名。
*   **解决方案**：在每个 `sentinel.conf` 文件中，强制开启主机名解析功能。

    ```properties
    sentinel resolve-hostnames yes
    sentinel announce-hostnames yes
    ```

### 问题 2：主机上的客户端无法连接 (DNS 错误)

*   **症状**：在主机上运行的 Python 脚本报错 `nodename nor servname provided, or not known`。
*   **根源**：Sentinel 向客户端通告了主节点的 Docker 内部主机名 (`redis-master`)，但主机的操作系统无法解析这个地址。
*   **解决方案**：修改主机的 `/etc/hosts` 文件，手动建立 `redis-master` 到 `127.0.0.1` 的映射关系。

### 问题 3：主机上的客户端无法连接 (Timeout 错误)

*   **症状**：解决了 DNS 问题后，Python 脚本又报 `Timeout connecting to server`。
*   **根源**：Python 的 `redis` 库客户端默认的连接超时时间较短（例如 0.5 秒），在某些情况下不足以完成连接的建立。
*   **解决方案**：在创建 Redis 客户端时，手动指定一个更长的超时时间，例如 `socket_timeout=5`。

---

## 3. 附录：常用命令指南

#### Redis 常用命令 (`redis-cli`)

| 分类 | 命令 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| **键 (Key)** | `KEYS` | `KEYS 'user:*'` | 查找匹配模式的键（**生产环境慎用**）。 |
| | `DEL` | `DEL mykey` | 删除一个或多个键。 |
| | `EXPIRE` | `EXPIRE mykey 60` | 为键设置 60 秒的过期时间。 |
| **字符串** | `SET` | `SET user:1 'Alice'` | 设置键的值。 |
| | `GET` | `GET user:1` | 获取键的值。 |
| **哈希** | `HSET` | `HSET user:1 name "Bob"` | 在哈希中设置一个字段。 |
| | `HGET` | `HGET user:1 name` | 获取哈希中一个字段的值。 |
| **列表** | `LPUSH` | `LPUSH tasks "task1"` | 从列表左侧推入一个值。 |
| | `RPOP` | `RPOP tasks` | 从列表右侧弹出一个值。 |
| **分布式锁** | `SET` | `SET lock key NX PX 30000` | (原子操作) 如果 key 不存在，则设置它并给 30 秒过期时间。 |
| **服务端** | `PING` | `PING` | 测试与服务器的连接。 |
| | `INFO` | `INFO replication` | 获取服务器的信息。 |
| | `SENTINEL`| `SENTINEL master mymaster` | 获取主节点信息。 |

#### Docker 常用指令

| 分类 | 命令 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| **容器生命周期** | `docker run` | `docker run -d -p 80:80 nginx` | 创建并启动一个容器。 |
| | `docker stop` | `docker stop my_container` | 停止一个正在运行的容器。 |
| | `docker rm` | `docker rm my_container` | 删除一个或多个容器。 |
| **状态与调试** | `docker ps` | `docker ps -a` | 列出容器。 |
| | `docker logs` | `docker logs -f my_container` | 查看容器的日志。 |
| | `docker exec` | `docker exec -it my_container /bin/sh` | 在运行的容器中执行命令。 |
| **Docker Compose** | `docker-compose up` | `docker-compose up -d` | 创建并启动所有服务。 |
| | `docker-compose down`| `docker-compose down -v` | 停止并删除所有服务、网络、数据卷。 |
| | `docker-compose ps` | `docker-compose ps` | 列出项目中的所有容器状态。 |
