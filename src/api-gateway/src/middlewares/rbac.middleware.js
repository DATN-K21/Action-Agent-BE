const RBACService = require('../services/rbac.service');

class RBACMiddleware {
    async validateApiKey(req, res, next) {
        const { subSystem, user } = req; // Assume `user` is added by authentication middleware
        const resource = req.path; // Use request path as resource
        const action = req.method; // Map HTTP methods to actions

        try {
            const hasPermission = await RBACService.checkPermissions({ user, subSystem, resource, action });
            if (!hasPermission) {
                return res.status(403).json({ error: 'Access denied' });
            };

            next();
        } catch (err) {
            next(err);
        }
    }
}

module.exports = new RBACMiddleware();