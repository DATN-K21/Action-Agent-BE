require('dotenv').config();

const GENERAL_CONFIGS = {
  ENABLE_HTTPS: process.env.ENABLE_HTTPS === 'true',
  PORT: process.env.PORT || 15000,
};

module.exports = GENERAL_CONFIGS;