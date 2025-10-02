// order-consumer.js
/**
 * 订单消费者服务
 * 这是一个在后台独立运行的进程，专门负责处理来自 Kafka 的订单消息。
 * 它的存在是整个系统异步架构的核心，实现了下单操作的削峰填谷和与 API 服务器的解耦。
 */
require('dotenv').config();
const db = require('./db');
const redisClient = require('./redisClient');
const { consumer } = require('./kafka');

/**
 * @function processOrder
 * @description 处理单条订单消息的函数。
 * @param {object} orderData - 包含 productId 和 quantity 的订单信息。
 * @why 为什么这个函数可以不用再检查库存？
 *      因为 API 层的 Redis 预扣减步骤已经确保了库存是足够的。消费者可以“信任”这个消息，
 *      并直接执行数据库写入操作。这大大简化了消费者的逻辑，使其职责更单一。
 * @why 为什么这里也要用事务？
 *      同理，"扣减SQL库存"和"创建订单记录"两个操作必须是原子性的。事务能保证这两个操作
 *      在数据库层面的一致性。
 */
const processOrder = async ({ productId, quantity }) => {
  console.log(`[Consumer] 收到已预留库存的订单消息: Product #${productId}, Quantity: ${quantity}`);
  let connection;
  try {
    connection = await db.getConnection();
    await connection.beginTransaction();

    // 步骤 1: 在数据库中真实地扣减库存
    await connection.query('UPDATE products SET stock = stock - ? WHERE id = ?', [quantity, productId]);
    // 步骤 2: 在数据库中创建订单记录
    await connection.query('INSERT INTO orders (product_id, quantity) VALUES (?, ?)', [productId, quantity]);
    
    await connection.commit();

    console.log(`[Consumer] 订单处理成功: Product #${productId} 的 SQL 库存已同步。`);

    // 步骤 3: 清理 Redis 中的商品详情缓存（不是库存缓存）。
    // @why 为什么要清理这个缓存？
    //      因为库存变化了，缓存中旧的商品信息（包含旧的 stock 值）已经过时。
    //      删除它能确保下次用户查询该商品时，能从数据库获取到最新的信息。
    const productInfoCacheKey = `product:${productId}`;
    await redisClient.del(productInfoCacheKey);
    console.log(`[Consumer] Redis 商品信息缓存已更新: ${productInfoCacheKey}`);

  } catch (error) {
    if (connection) await connection.rollback();
    // @critical 在生产环境中，这里的错误处理至关重要。如果处理失败，
    //           不能简单地丢弃消息。应该将该消息移入“死信队列”(Dead-Letter Queue)，
    //           以便后续进行人工干预或自动重试，防止订单丢失。
  } finally {
    if (connection) connection.release();
  }
};

/**
 * @function run
 * @description 消费者服务的启动和主运行循环。
 */
const run = async () => {
  // 消费者也需要连接 Redis 来执行缓存清理操作
  await redisClient.connect(); 
  await consumer.connect();
  // 订阅 'orders_topic' 主题
  await consumer.subscribe({ topic: 'orders_topic', fromBeginning: true });
  console.log('Kafka Consumer connected and subscribed.');

  // 启动消费者，并为每条消息调用 processOrder 函数
  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const orderData = JSON.parse(message.value.toString());
      await processOrder(orderData);
    },
  });
};

run().catch(console.error);