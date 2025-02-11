require('dotenv').config();

const ENDPOINT_CONFIGS = {
    USER_SERVICE_URL: process.env.USER_SERVICE_URL,
    // LOG_SERVICE_URL: process.env.LOG_SERVICE_URL,
    // RABBITMQ_URL: process.env.RABBITMQ_URL,
    // ELASTICSEARCH_URL: process.env.ELASTICSEARCH_URL,
    // REDIS_URL: process.env.REDIS_URL,
}

module.exports = ENDPOINT_CONFIGS;