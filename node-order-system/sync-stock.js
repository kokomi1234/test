// sync-stock.js
// 一次性脚本，用于将 MySQL 中的商品库存同步到 Redis

const db = require('./db');
const redisClient = require('./redisClient');

const syncStock = async () => {
  console.log('开始同步库存到 Redis...');
  try {
    await redisClient.connect();
    const [products] = await db.query('SELECT id, stock FROM products');

    if (products.length === 0) {
      console.log('数据库中没有商品，无需同步。');
      return;
    }

    const pipeline = redisClient.multi();
    for (const product of products) {
      const stockKey = `stock:product:${product.id}`;
      pipeline.set(stockKey, product.stock);
    }
    await pipeline.exec();

    console.log(`✅ 库存同步成功！共同步了 ${products.length} 件商品。`);

  } catch (error) {
    console.error('❌ 库存同步失败:', error);
  } finally {
    await redisClient.quit();
    await db.end();
  }
};

syncStock();
