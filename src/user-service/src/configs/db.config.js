require('dotenv').config();

const dbConfig = {
    mongoDB: {
        maxPoolSize: process.env.MONGODB_MAX_POOL_SIZE,
    },
    postgreSQL: {
        user: process.env.POSTGRESQL_USER,
        password: process.env.POSTGRESQL_PASSWORD,
        host: process.env.POSTGRESQL_HOST,
        port: process.env.POSTGRESQL_PORT,
        database: process.env.POSTGRESQL_DATABASE,
        maxPoolSize: process.env.POSTGRES_MAX_POOL_SIZE,
    },
}

module.exports = dbConfig;