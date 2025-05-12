require('dotenv').config();

const GENERAL_CONFIGS = {
  HTTPS_PORT: process.env.HTTPS_PORT || 15000,
};

module.exports = GENERAL_CONFIGS;