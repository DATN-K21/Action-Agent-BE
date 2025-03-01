require('dotenv').config();

const GENERAL_CONFIGS = {
  HTTP_PORT: process.env.HTTP_PORT || 8300,
  HTTPS_PORT: process.env.HTTPS_PORT || 8301,
};

module.exports = GENERAL_CONFIGS;