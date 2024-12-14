require('dotenv').config();

const USER_SERVICE_URL = process.env.USER_SERVICE_URL;

module.exports = {
    GET_SUBSYSTEM_BY_APIKEY_URL: `${USER_SERVICE_URL}/api/v1/subsystem/:apiKey`,
    CHECK_PERMISSION_URL: `${USER_SERVICE_URL}/api/v1/permission`,
}
