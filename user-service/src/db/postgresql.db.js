const { Client } = require("pg")
const { postgreSQL: pgConfig } = require("../configs/db.config");

const setupPostgreSQL = async () => { 
    const client = new Client({
        user: pgConfig.user,
        password: pgConfig.password,
        host: pgConfig.host,
        port: pgConfig.port,
        database: pgConfig.database,
    })
    await client.connect();
}

module.exports = setupPostgreSQL;