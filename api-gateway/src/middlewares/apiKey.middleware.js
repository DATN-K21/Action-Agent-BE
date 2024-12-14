const RBACService = require('../services/rbac.service');

class ApiKeyMiddleware {
    async validateApiKey(req, res, next) {
        const apiKey = req.headers['x-api-key'];
        if (!apiKey) {
            return res.status(401).json({ error: 'API key missing' });
        };

        try {
            const subSystem = await RBACService.getSubSystemByApiKey(apiKey);
            if (!subSystem) return res.status(403).json({ error: 'Invalid API key' });

            req.subSystem = subSystem; // Attach subsystem data to request
            next();
        } catch (err) {
            next(err);
        }
    }
}

module.exports = new ApiKeyMiddleware();
