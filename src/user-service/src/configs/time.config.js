require('dotenv').config();

const timeConfig = {
    access_token_expire: process.env.ACCESS_TOKEN_EXPIRE || '15m',
    refresh_token_expire: process.env.REFRESH_TOKEN_EXPIRE || '1d',
    cookie_expire: process.env.COOKIE_EXPIRE || 15 * 60 * 1000,
    reset_password_token_expire: process.env.RESET_PASSWORD_EXPIRE || '5m',
    activation_token_expire: process.env.ACTIVATION_TOKEN_EXPIRE || '15m',
};

module.exports = timeConfig;