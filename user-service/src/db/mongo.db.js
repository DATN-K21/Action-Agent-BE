
const mongoose = require("mongoose");
require("dotenv").config();
const { mongoDB: mongoConfig } = require("../configs/db.config");
const seedRoles = require("../modules/role/role.seed");
const seedResources = require("../modules/resource/resource.seed");

const { maxPoolSize: MAX_POOL_SIZE } = mongoConfig;
const connectString = process.env.MONGODB_CONNECTION_STRING;

const setupMongoDB = async () => {
    console.log(connectString);
    mongoose.connect(connectString, {
        maxPoolSize: MAX_POOL_SIZE,
        connectTimeoutMS: 60000
    })
        .then(async () => {
            console.log("Connect to MongoDB successfully");
            try {
                const seededRoleNumber = await seedRoles(mongoose);
                const seededResourceNumber = await seedResources(mongoose);
                console.log(`Seeded ${seededRoleNumber} roles and ${seededResourceNumber} resources successfully.`);
            } catch (error) {
                console.error("Error seeding data:", error);
            }
            }).catch(err => console.log("Error connecting to MongoDB: " + err))
}

module.exports = setupMongoDB;
