const axios = require('axios');

const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8001';

async function getUserById(id) {
    const response = await axios.get(`${USER_SERVICE_URL}/users/${id}`);
    return response.data;
}

module.exports = { getUserById };
