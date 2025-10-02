// kafka.js
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'order-app',
  brokers: ['localhost:9092']
});

const producer = kafka.producer();
const consumer = kafka.consumer({ groupId: 'order-group' });

module.exports = { kafka, producer, consumer };