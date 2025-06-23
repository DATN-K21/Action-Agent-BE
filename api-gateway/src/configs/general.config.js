require('dotenv').config();

const GENERAL_CONFIGS = {
  ENABLE_HTTPS: process.env.ENABLE_HTTPS === 'true',
  PORT: parseInt(process.env.PORT, 10) || 15000,
};

module.exports = GENERAL_CONFIGS;