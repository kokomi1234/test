// order-consumer.js
require('dotenv').config();
const db = require('./db');
const redisClient = require('./redisClient');
const { consumer } = require('./kafka');

const processOrder = async ({ productId, quantity }) => {
  console.log(`[Consumer] 收到已预留库存的订单消息: Product #${productId}, Quantity: ${quantity}`);
  let connection;
  try {
    connection = await db.getConnection();
    await connection.beginTransaction();

    // 直接扣减 SQL 库存并创建订单，因为 Redis 已确保库存足够
    await connection.query('UPDATE products SET stock = stock - ? WHERE id = ?', [quantity, productId]);
    await connection.query('INSERT INTO orders (product_id, quantity) VALUES (?, ?)', [productId, quantity]);
    
    await connection.commit();

    console.log(`[Consumer] 订单处理成功: Product #${productId} 的 SQL 库存已同步。`);

    // 清理商品信息缓存（注意不是库存缓存）
    const productInfoCacheKey = `product:${productId}`;
    await redisClient.del(productInfoCacheKey);
    console.log(`[Consumer] Redis 商品信息缓存已更新: ${productInfoCacheKey}`);

  } catch (error) {
    if (connection) await connection.rollback();
    console.error("[Consumer] 处理订单时发生错误:", error);
    // 在实际生产中，这里应有错误处理和重试逻辑，例如将失败的消息移入死信队列
  } finally {
    if (connection) connection.release();
  }
};

const run = async () => {
  await redisClient.connect(); // 消费者也需要连接 Redis 来清理缓存
  await consumer.connect();
  await consumer.subscribe({ topic: 'orders_topic', fromBeginning: true });
  console.log('Kafka Consumer connected and subscribed.');

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const orderData = JSON.parse(message.value.toString());
      await processOrder(orderData);
    },
  });
};

run().catch(console.error);