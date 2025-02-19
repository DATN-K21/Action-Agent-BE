const express = require('express');
const { initRabbitMQ } = require('./services/rabbitmq.service');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const morgan = require('morgan');

const app = express();

// Middleware

app.use(morgan("dev"))
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(rateLimit({ windowMs: 60 * 1000, max: 50 })); // 50 requests per minute

// Routes
app.get('/', (req, res) => {
    res.send('My AI Assistant API Gateway is listening!');
});
app.get('/health', (req, res) => {
    res.json({ status: 'UP!' });
});

app.use('/', require("./routes/index"));

// initRabbitMQ().catch(console.error);

module.exports = app;
