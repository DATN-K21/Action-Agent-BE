require('dotenv').config();

const TIME_CONFIGS = {
  MICROSERVICE_TIMEOUT: +process.env.MICROSERVICE_TIMEOUT || 300000, // 5 minutes
}

module.exports = TIME_CONFIGS;