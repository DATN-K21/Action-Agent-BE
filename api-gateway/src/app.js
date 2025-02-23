const express = require('express');
// const { initRabbitMQ } = require('./services/rabbitmq.service');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const morgan = require('morgan');

const app = express();

// Set trust proxy for Azure environment
app.set('trust proxy', 1);

// Rate limiter middleware
const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 50, // 50 requests per minute
    keyGenerator: (req) => req.ip, // Use req.ip instead of X-Forwarded-For
    handler: (req, res) => {
        res.status(429).json({ error: "Too many requests. Please try again later." });
    }
});

// Middleware
app.use(morgan("dev"));
app.use(cors());
app.use(express.json());
app.use(limiter); // Apply rate limiter

// Routes
app.get('/', (req, res) => {
    res.send('My AI Assistant API Gateway is listening!');
});
app.get('/health', (req, res) => {
    res.json({ status: 'UP!' });
});

// Main API routes
app.use('/', require("./routes/index"));

// Initialize RabbitMQ
// initRabbitMQ().catch(err => {
//     console.error("RabbitMQ initialization failed:", err);
// });

module.exports = app;
