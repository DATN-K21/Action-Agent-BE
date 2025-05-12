const amqp = require('amqplib');
require('dotenv').config();
let channel;

const initRabbitMQ = async () => {
    const connection = await amqp.connect(process.env.RABBITMQ_URL);
    channel = await connection.createChannel();
    console.log('RabbitMQ Connected');
};

const publishMessage = async (queue, message) => {
    await channel.assertQueue(queue);
    channel.sendToQueue(queue, Buffer.from(JSON.stringify(message)));
};

const consumeMessage = async (queue, callback) => {
    await channel.assertQueue(queue);
    channel.consume(queue, (msg) => {
        callback(JSON.parse(msg.content.toString()));
        channel.ack(msg);
    });
};

module.exports = { initRabbitMQ, publishMessage, consumeMessage };
