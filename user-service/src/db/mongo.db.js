
const mongoose = require("mongoose");
require("dotenv").config();
const { mongoDB: mongoConfig } = require("../configs/db.config");

const { maxPoolSize: MAX_POOL_SIZE } = mongoConfig;
const connectString = process.env.MONGODB_CONNECTION_STRING;

const setupMongoDB = async () => {
    mongoose.connect(connectString, { maxPoolSize: MAX_POOL_SIZE })
        .then(_ => {
            console.log("Connect to MongoDB successfully");
        }).catch(err => console.log("Error connecting to MongoDB: " + err))
}

module.exports = setupMongoDB;
