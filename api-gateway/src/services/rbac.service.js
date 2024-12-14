const RedisService = require('./redis.service');
const axios = require('axios');
const { GET_SUBSYSTEM_BY_APIKEY_URL, CHECK_PERMISSION_URL } = require("../configs/endpoint.config");
const SubSystemUtil = require('../utils/subsystem.utils');

class RBACService {
    static async getSubSystemByApiKey(apiKey) {
        const cacheKey = `subsystem:${apiKey}`;
        const cached = await RedisService.getCache(cacheKey);

        if (cached) return cached;

        // const url = GET_SUBSYSTEM_BY_APIKEY_URL.replace(':apiKey', apiKey);
        // const response = await axios.get(url);
        const data = SubSystemUtil.getSubSystemByApiKey(apiKey);
        if (!data || !data?.id || !data?.slug || !data?.name) {
            throw new Error("Invalid API key");
        }

        await RedisService.setCache(cacheKey, data, 3600); // Cache for 1 hour
        return data;
    }

    static async checkPermissions({ user, subSystem, resource, action }) {
        const cacheKey = `rbac:${user.role}:${resource}:${action}`;
        const cached = await RedisService.getCache(cacheKey);

        if (cached !== null) {
            return cached;
        }

        // const url = CHECK_PERMISSION_URL;
        // const response = await axios.post(url, {
        //     user,
        //     subSystem,
        //     resource,
        //     action,
        // });
        const data = SubSystemUtil

        await RedisService.setCache(cacheKey, response.data.allowed, 600); // Cache for 10 minutes
        return response.data.allowed;
    }
}

const getSubSystemByApiKey = async (apiKey) => {
    const cacheKey = `subsystem:${apiKey}`;
    const cached = await getCache(cacheKey);

    if (cached) return cached;

    const response = await axios.get(`http://user-service/api/subsystems/${apiKey}`);
    await setCache(cacheKey, response.data, 3600); // Cache for 1 hour
    return response.data;
};

module.exports = RBACService;
