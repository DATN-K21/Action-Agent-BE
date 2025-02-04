const express = require('express');
const passport = require('passport');
require('dotenv').config();
const cors = require('cors');

const app = express();

app.set('view engine', 'ejs');
app.set('views', __dirname + '/modules/access/views');

app.use(cors());
// Initialize Passport
app.use(passport.initialize());


const morgan = require('morgan');
const { default: helmet } = require('helmet');
const compression = require('compression');

//init middlewares
app.use(morgan("dev"))
app.use(express.json())
app.use(express.urlencoded({ extended: true }));

app.use(helmet())
app.use(compression())

//init db
require('./db/mongo.db')();

//init routing
app.use('/', require('./routes/index'));

//handle errors
app.use((req, res, next) => {
    const error = new Error('Not Found');
    error.status = 404;
    next(error);
})

app.use((error, req, res, next) => {
    const statusCode = error?.status ?? 500;
    return res.status(statusCode).json({
        status: statusCode,
        code: error?.code,
        message: error.message ?? 'Internal Server Error',
        errorStack: process.env.NODE_ENV === "dev" ? error?.stack : undefined, //Dev mode only
    })
})


module.exports = app;