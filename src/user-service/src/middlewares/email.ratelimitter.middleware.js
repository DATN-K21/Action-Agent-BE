require('dotenv').config();
const rateLimit = require('express-rate-limit');
const { RedisStore } = require('rate-limit-redis');
const { createClient } = require('redis');

const REDIS_HOST = process.env.REDIS_HOST || 'redis';
const REDIS_PORT = process.env.REDIS_PORT || '6379';
const REDIS_PASSWORD = process.env.REDIS_PASSWORD || 'root';
const REDIS_USER = process.env.REDIS_USER || 'default';

const redisUrl = `redis://${REDIS_USER}:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}`;
const redisClient = createClient({
    url: redisUrl,
});


redisClient.connect().catch(console.error);

const emailRateLimiter = rateLimit({
    store: new RedisStore({
        sendCommand: (...args) => redisClient.sendCommand(args),
    }),
    windowMs: 60 * 60 * 1000,
    max: 3, // Limit each IP to 3 requests per hour
    keyGenerator: (req) => req.ip,
    message: {
        status: 429,
        error: 'Too many requests',
        message: 'You have exceeded the maximum number of email requests. Please try again later.',
    },
    standardHeaders: true,
    legacyHeaders: false,
});

module.exports = emailRateLimiter;
