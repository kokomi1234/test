// redisClient.js
const redis = require('redis');
require('dotenv').config();

// 从环境变量中读取集群节点地址，并解析
const clusterNodes = process.env.REDIS_CLUSTER_NODES.split(',').map(url => ({ url }));

// 只创建和导出客户端实例，不在此处连接
const redisClient = redis.createClient({
  cluster: {
    rootNodes: clusterNodes,
  }
});

redisClient.on('error', (err) => console.error('Redis Cluster Client Error', err));

module.exports = redisClient;
