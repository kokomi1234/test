// index.js
require('dotenv').config();
const express = require('express');
const db = require('./db');
const redisClient = require('./redisClient');
const { producer } = require('./kafka');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

// --- Product Routes ---

app.get('/products/:id', async (req, res) => {
  const { id } = req.params;
  const cacheKey = `product:${id}`;
  try {
    const cachedProduct = await redisClient.get(cacheKey);
    if (cachedProduct) {
      return res.json({ source: 'cache', data: JSON.parse(cachedProduct) });
    }
    const [rows] = await db.query('SELECT * FROM products WHERE id = ?', [id]);
    const product = rows[0];
    if (!product) {
      return res.status(404).json({ error: '商品不存在' });
    }
    await redisClient.set(cacheKey, JSON.stringify(product), { EX: 3600 });
    res.json({ source: 'database', data: product });
  } catch (error) {
    console.error("获取商品信息时出错:", error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

app.get('/products', async (req, res) => {
  try {
    const [rows] = await db.query('SELECT * FROM products ORDER BY id DESC');
    res.json({ data: rows });
  } catch (error) {
    console.error("获取所有商品时出错:", error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

app.post('/products', async (req, res) => {
  const { name, stock, imageUrl } = req.body;
  if (!name || stock === undefined || stock < 0) {
    return res.status(400).json({ error: '无效的商品名称或库存' });
  }
  try {
    const [result] = await db.query('INSERT INTO products (name, stock, image_url) VALUES (?, ?, ?)', [name, stock, imageUrl || null]);
    const newProduct = { id: result.insertId, name, stock, image_url: imageUrl || null };
    
    // 将新商品库存写入 Redis
    await redisClient.set(`stock:product:${newProduct.id}`, stock);

    console.log(`[DB & Redis] 已创建新商品: ${name}`);
    res.status(201).json({ message: '商品创建成功', data: newProduct });
  } catch (error) {
    console.error("创建商品时出错:", error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

app.delete('/products/:id', async (req, res) => {
  const { id } = req.params;
  try {
    const [orders] = await db.query('SELECT id FROM orders WHERE product_id = ? LIMIT 1', [id]);
    if (orders.length > 0) {
      return res.status(400).json({ error: '无法删除，该商品存在关联订单' });
    }
    const [result] = await db.query('DELETE FROM products WHERE id = ?', [id]);
    if (result.affectedRows === 0) {
      return res.status(404).json({ error: '商品未找到' });
    }
    
    // 从 Redis 中删除商品信息和库存缓存
    await redisClient.del([`product:${id}`, `stock:product:${id}`]);

    console.log(`[DB & Redis] 商品 ${id} 已被删除。`);
    res.status(200).json({ message: '商品删除成功' });
  } catch (error) {
    console.error(`删除商品 ${id} 时出错:`, error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

// --- Order Routes ---

app.post('/orders', async (req, res) => {
  const { productId, quantity } = req.body;
  if (!productId || !quantity || quantity <= 0) {
    return res.status(400).json({ error: '无效的请求参数' });
  }

  const stockKey = `stock:product:${productId}`;

  try {
    // 1. 在 Redis 中原子性地预扣减库存
    const newStock = await redisClient.decrBy(stockKey, quantity);

    // 2. 检查库存是否足够
    if (newStock < 0) {
      // 超卖，立即归还库存并报错
      await redisClient.incrBy(stockKey, quantity);
      console.log(`[API] 库存预扣减失败: Product #${productId}`);
      return res.status(400).json({ error: '库存不足' });
    }

    // 3. 预扣减成功，将订单请求发送到 Kafka
    await producer.send({
      topic: 'orders_topic',
      messages: [{ value: JSON.stringify({ productId, quantity }) }],
    });

    console.log(`[API] 库存预扣减成功，订单请求已发送到 Kafka: Product #${productId}`);
    res.status(202).json({ message: '订单请求已接受，正在处理中' });

  } catch (error) {
    console.error("处理订单请求时出错:", error);
    // 这里的错误处理需要更精细，例如如果 producer.send 失败，需要将 Redis 库存归还
    res.status(500).json({ error: '服务器内部错误' });
  }
});

app.get('/orders', async (req, res) => {
  try {
    const [orders] = await db.query(`SELECT o.id, o.quantity, o.order_date, p.name as productName FROM orders o JOIN products p ON o.product_id = p.id ORDER BY o.order_date DESC`);
    res.json({ data: orders });
  } catch (error) {
    console.error("获取订单列表时出错:", error);
    res.status(500).json({ error: '服务器内部错误' });
  }
});

app.delete('/orders/:id', async (req, res) => {
  let connection;
  const { id } = req.params;
  try {
    connection = await db.getConnection();
    await connection.beginTransaction();
    const [rows] = await connection.query('SELECT product_id, quantity FROM orders WHERE id = ?', [id]);
    const order = rows[0];
    if (!order) {
      await connection.rollback();
      return res.status(404).json({ error: '订单未找到' });
    }
    // 归还 SQL 库存
    await connection.query('UPDATE products SET stock = stock + ? WHERE id = ?', [order.quantity, order.product_id]);
    await connection.query('DELETE FROM orders WHERE id = ?', [id]);
    await connection.commit();
    
    // 同时归还 Redis 库存
    await redisClient.incrBy(`stock:product:${order.product_id}`, order.quantity);
    // 清理商品信息缓存
    await redisClient.del(`product:${order.product_id}`);

    console.log(`[DB & Redis] 订单 ${id} 已被撤回，库存已归还。`);
    res.status(200).json({ message: '订单撤回成功' });
  } catch (error) {
    if (connection) await connection.rollback();
    console.error(`撤回订单 ${id} 时出错:`, error);
    res.status(500).json({ error: '服务器内部错误' });
  } finally {
    if (connection) connection.release();
  }
});

// --- Server Start ---

const startServer = async () => {
  try {
    await redisClient.connect();
    console.log('Redis Client connected for API Server.');
    await producer.connect();
    console.log('Kafka Producer connected.');
    app.listen(PORT, () => {
      console.log(`API 服务器正在 http://localhost:${PORT} 上运行`);
    });
  } catch (error) {
    console.error("启动 API 服务器失败:", error);
    process.exit(1);
  }
};

startServer();
