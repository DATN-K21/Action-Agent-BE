const redis = require('redis');

client = redis.createClient({ url: process.env.REDIS_URL });
client.on('error', (err) => console.error('Redis Client Error: ', err));
client.connect();

class RedisService {
    static async setCache(key, value, ttl) {
        this.client.set(key, JSON.stringify(value), 'EX', ttl);
    }

    static async getCache(key) {
        const data = await this.client.get(key);
        return data ? JSON.parse(data) : null;
    }
}

module.exports = RedisService;
