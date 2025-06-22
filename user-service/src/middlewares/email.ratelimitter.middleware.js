require('dotenv').config();
const rateLimit = require('express-rate-limit');
const { RedisStore } = require('rate-limit-redis');
const { createClient } = require('redis');

const redisUrl = process.env.REDIS_URL || 'redis://default:root@redis:6379';
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
