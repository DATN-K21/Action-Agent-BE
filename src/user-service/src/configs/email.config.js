require('dotenv').config();

const emailConfig = {
    user: process.env.EMAIL_USERNAME,
    pass: process.env.EMAIL_PASSWORD,

}

module.exports = emailConfig;