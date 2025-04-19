
const mongoose = require("mongoose");
require("dotenv").config();
const { mongoDB: mongoConfig } = require("../configs/db.config");
const seedRoles = require("../modules/role/role.seed");

const { maxPoolSize: MAX_POOL_SIZE } = mongoConfig;
const connectString = process.env.MONGODB_CONNECTION_STRING;

const setupMongoDB = async () => {
    mongoose.connect(connectString, { maxPoolSize: MAX_POOL_SIZE })
        .then(async () => {
            await seedRoles(mongoose);
            console.log("Connect to MongoDB successfully");
        }).catch(err => console.log("Error connecting to MongoDB: " + err))
}

module.exports = setupMongoDB;
