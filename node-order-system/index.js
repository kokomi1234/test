// index.js
/**
 * 核心 API 服务器
 * 负责处理所有面向用户的 HTTP 请求，包括商品管理和订单创建。
 * 它是系统与用户交互的主要入口。
 */
require('dotenv').config();
const express = require('express');
const db = require('./db');
const redisClient = require('./redisClient');
const { producer } = require('./kafka');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// --- 商品相关路由 (Product Routes) ---

/**
 * @route GET /products/:id
 * @description 获取单个商品详情。
 * @goal 实现“缓存旁路”模式 (Cache-Aside Pattern)。
 * @why 为什么优先查 Redis？
 *      为了减少对主数据库的访问压力。商品详情等不频繁变更的数据非常适合缓存。
 *      这可以极大地提升读取性能并降低数据库负载。
 */
app.get('/products/:id', async (req, res) => {
  const { id } = req.params;
  const cacheKey = `product:${id}`;
  try {
    // 1. 尝试从 Redis 缓存中获取数据
    const cachedProduct = await redisClient.get(cacheKey);
    if (cachedProduct) {
      return res.json({ source: 'cache', data: JSON.parse(cachedProduct) });
    }

    // 2. 如果缓存未命中，则查询数据库
    const [rows] = await db.query('SELECT * FROM products WHERE id = ?', [id]);
    const product = rows[0];
    if (!product) {
      return res.status(404).json({ error: '商品不存在' });
    }

    // 3. 将从数据库查到的数据写入缓存，并设置过期时间 (e.g., 1小时)
    // @why 设置过期时间？ 防止数据不一致。如果商品信息在数据库中被修改，缓存最终会过期，
    //      从而强制下次请求重新从数据库加载最新数据。
    await redisClient.set(cacheKey, JSON.stringify(product), { EX: 3600 });
    res.json({ source: 'database', data: product });
  } catch (error) {
    console.error("获取商品信息时出错:", error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

/**
 * @route POST /products
 * @description 创建一个新商品。
 * @why 为什么要在创建商品时就操作 Redis？
 *      因为本系统的库存最终一致性依赖于 Redis。创建商品时，必须将其初始库存同步写入 Redis，
 *      为后续的“库存预扣减”做好准备。这确保了 Redis 始终持有权威的库存数据。
 */
app.post('/products', async (req, res) => {
  const { name, stock, imageUrl } = req.body;
  if (!name || stock === undefined || stock < 0) {
    return res.status(400).json({ error: '无效的商品名称或库存' });
  }
  try {
    const [result] = await db.query('INSERT INTO products (name, stock, image_url) VALUES (?, ?, ?)', [name, stock, imageUrl || null]);
    const newProduct = { id: result.insertId, name, stock, image_url: imageUrl || null };
    
    // 关键步骤：将新商品的库存信息同步到 Redis
    await redisClient.set(`stock:product:${newProduct.id}`, stock);

    console.log(`[DB & Redis] 已创建新商品: ${name}`);
    res.status(201).json({ message: '商品创建成功', data: newProduct });
  } catch (error) {
    console.error("创建商品时出错:", error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});


// --- 订单相关路由 (Order Routes) ---

/**
 * @route POST /orders
 * @description 创建一个新订单 (下单)。这是整个系统的核心和最复杂的部分。
 * @goal 解决高并发下的“超卖”问题，并提供快速的用户响应。
 * @why 采用“Redis预扣减库存 + Kafka消息队列”的异步架构？
 *      1. 避免竞态条件 (Race Condition): 直接操作数据库在高并发下会产生超卖。而 Redis 的 DECRBY 是原子操作，
 *         能确保在任何瞬间只有一个请求能成功扣减库存，从根本上解决了竞态问题。
 *      2. 提升用户体验: API 无需等待缓慢的数据库写入操作。它在 Redis 中快速完成库存检查和预扣减后，
 *         立即将订单任务抛给 Kafka 并向用户返回“处理中”的响应。这使得 API 响应速度极快。
 *      3. 增强系统韧性 (Resilience): 即使后端数据库暂时宕机，订单请求也会安全地积压在 Kafka 中，
 *         待数据库恢复后由消费者继续处理，避免了数据丢失。
 */
app.post('/orders', async (req, res) => {
  const { productId, quantity } = req.body;
  if (!productId || !quantity || quantity <= 0) {
    return res.status(400).json({ error: '无效的请求参数' });
  }

  const stockKey = `stock:product:${productId}`;

  try {
    // 步骤 1: 在 Redis 中进行原子性的“预扣减”库存
    const newStock = await redisClient.decrBy(stockKey, quantity);

    // 步骤 2: 检查库存是否足够 (扣减后库存是否小于 0)
    if (newStock < 0) {
      // 库存不足，发生了超卖。必须立即将刚刚减掉的库存加回去，以修正数据。
      await redisClient.incrBy(stockKey, quantity);
      console.log(`[API] 库存预扣减失败: Product #${productId}`);
      return res.status(400).json({ error: '库存不足' });
    }

    // 步骤 3: 预扣减成功，证明库存充足。此时将订单消息安全地发送到 Kafka 队列，等待后台消费者处理。
    await producer.send({
      topic: 'orders_topic',
      messages: [{ value: JSON.stringify({ productId, quantity }) }],
    });

    console.log(`[API] 库存预扣减成功，订单请求已发送到 Kafka: Product #${productId}`);
    // 返回 202 Accepted 状态码，表示请求已被接受，但仍在后台处理中。
    res.status(202).json({ message: '订单请求已接受，正在处理中' });

  } catch (error) {
    console.error("处理订单请求时出错:", error);
    // @critical 这里的错误处理很重要。如果 Redis 成功但 Kafka 发送失败，
    //           理论上需要将 Redis 的库存归还，以防止数据不一致。
    //           在生产环境中，这需要一个更健壮的回滚或重试机制。
    res.status(500).json({ error: '服务器内部错误' });
  }
});

/**
 * @route DELETE /orders/:id
 * @description 撤回一个已创建的订单。
 * @why 为什么需要用数据库事务 (Transaction)？
 *      因为“归还库存”和“删除订单”是两个独立的操作，必须作为一个整体要么全部成功，要么全部失败。
 *      如果中途失败，事务可以回滚，防止出现“订单删了但库存没加回来”的数据不一致状态。
 * @why 为什么还要操作 Redis？
 *      因为 Redis 是库存的权威来源。数据库回滚后，必须同步更新 Redis 的库存计数，
 *      否则用户看到的库存量将是错误的。
 */
app.delete('/orders/:id', async (req, res) => {
  let connection;
  const { id } = req.params;
  try {
    // 获取一个数据库连接，并开启事务
    connection = await db.getConnection();
    await connection.beginTransaction();

    // 1. 查找订单以获取商品ID和数量
    const [rows] = await connection.query('SELECT product_id, quantity FROM orders WHERE id = ?', [id]);
    const order = rows[0];
    if (!order) {
      await connection.rollback();
      return res.status(404).json({ error: '订单未找到' });
    }
    
    // 2. 在事务中归还数据库库存
    await connection.query('UPDATE products SET stock = stock + ? WHERE id = ?', [order.quantity, order.product_id]);
    // 3. 在事务中删除订单
    await connection.query('DELETE FROM orders WHERE id = ?', [id]);
    
    // 提交事务，使上述操作永久生效
    await connection.commit();
    
    // 4. 事务成功后，同步归还 Redis 中的库存
    await redisClient.incrBy(`stock:product:${order.product_id}`, order.quantity);
    //    同时，删除可能存在的商品详情缓存，以确保下次读取时能获取到最新的库存信息。
    await redisClient.del(`product:${order.product_id}`);

    console.log(`[DB & Redis] 订单 ${id} 已被撤回，库存已归还。`);
    res.status(200).json({ message: '订单撤回成功' });
  } catch (error) {
    if (connection) await connection.rollback(); // 如果任何步骤失败，回滚所有数据库操作
    console.error(`撤回订单 ${id} 时出错:`, error);
    res.status(500).json({ error: '服务器内部错误' });
  } finally {
    if (connection) connection.release(); // 无论成功或失败，最后都要释放数据库连接
  }
});


// --- 服务器启动逻辑 ---
const startServer = async () => {
  try {
    // 必须先成功连接到 Redis 和 Kafka，再启动 Web 服务器
    await redisClient.connect();
    console.log('Redis Client connected for API Server.');
    await producer.connect();
    console.log('Kafka Producer connected.');
    app.listen(PORT, () => {
      console.log(`API 服务器正在 http://localhost:${PORT} 上运行`);
    });
  } catch (error) {
    console.error("启动 API 服务器失败:", error);
    process.exit(1); // 如果关键服务连接失败，则直接退出应用
  }
};

startServer();