require('dotenv').config();

const jwtConfig = {
    jwtSecret: process.env.JWT_SECRET
};

module.exports = jwtConfig;