require('dotenv').config();

const ENDPOINT_CONFIGS = {
    USER_SERVICE_URL: process.env.USER_SERVICE_URL,
    AI_SERVICE_URL: process.env.AI_SERVICE_URL,
    EXTENSION_SERVICE_URL: process.env.EXTENSION_SERVICE_URL,
    RABBITMQ_URL: process.env.RABBITMQ_URL,
    ELASTICSEARCH_URL: process.env.ELASTICSEARCH_URL,
    REDIS_URL: process.env.REDIS_URL,
}

module.exports = ENDPOINT_CONFIGS;