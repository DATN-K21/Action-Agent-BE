//Call api to sync data with other services
const axios = require('axios');
require("dotenv").config();

const syncData = async (path, data) => {
    try {
        const response = await axios.post(`${process.env.AI_SERVICE_URL}${path}`, data, {
            headers: {
                'Content-Type': 'application/json',
                'accept': 'application/json'
            }
        });
        return response.data;
    } catch (error) {
        return error;
    }
};

exports.syncData = syncData;