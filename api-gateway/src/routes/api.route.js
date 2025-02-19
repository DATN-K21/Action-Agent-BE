const router = require('express').Router();
const { createProxyMiddleware, fixRequestBody } = require('http-proxy-middleware');
const ENDPOINT_CONFIGS = require('../configs/endpoint.config');
const currentUserMiddleware = require('../middlewares/currentUser.middleware');

const serviceRegistry = {
    'user': ENDPOINT_CONFIGS.USER_SERVICE_URL,
    'log': ENDPOINT_CONFIGS.LOG_SERVICE_URL,
    'ai': ENDPOINT_CONFIGS.AI_SERVICE_URL,
};

Object.entries(serviceRegistry).forEach(([serviceName, target]) => {
    router.use(currentUserMiddleware);

    router.use(`/${serviceName}/*`,
        createProxyMiddleware({
            target,
            changeOrigin: true, // Adjust the host header to match the target
            pathRewrite: (path, req) => {
                const newPath = req.originalUrl;
                const rewrittenPath = newPath.replace(new RegExp(`^/api/v1/${serviceName}`), '/api/v1');
                console.log(`[DEBUG] Rewritten path: ${rewrittenPath}`);
                return rewrittenPath;
            },
            logLevel: 'debug', // Enable debug-level logging in the proxy
            timeout: 5000, // 5 seconds
            proxyTimeout: 5000, // 5 seconds
            on: {
                proxyReq: fixRequestBody,
                proxyRes(proxyRes, req, res) {
                    proxyRes.on('end', () => {
                        if (!res.headersSent) {
                            res.status(500).json({ error: `Failed to process request for service '${serviceName}'.` });
                        }
                    });
                }
            },
            onError(err, req, res) {
                console.error(`Proxy error for service '${serviceName}':`, err.message);
                res.status(500).json({ error: `Failed to process request for service '${serviceName}'.` });
            },
        })
    );
});

module.exports = router;
