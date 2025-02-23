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
            ws: true, // Proxy websockets
            pathRewrite: (path, req) => {
                const isWs = req.headers.upgrade && req.headers.upgrade.toLowerCase() === 'websocket';
                let originalPath = isWs ? (req.url || path) : (req.originalUrl || path);
                const rewrittenPath = serviceName == "ai"
                    ? originalPath.replace(new RegExp(`^/api/v1/${serviceName}`), '')
                    : originalPath.replace(new RegExp(`^/api/v1/${serviceName}`), '/api/v1');
                console.log("[HTTP] Rewritten path:", rewrittenPath);
                return rewrittenPath;
            },
            logLevel: 'debug', // Enable debug-level logging in the proxy
            timeout: 5000, // 5 seconds
            proxyTimeout: 5000, // 5 seconds
            on: {
                proxyReq: fixRequestBody,
            },
            onError(err, req, resOrSocket) {
                console.error(`Proxy error for service '${serviceName}':`, err.message);
                const isWs = req.headers.upgrade && req.headers.upgrade.toLowerCase() === 'websocket';
                if (isWs) {
                    resOrSocket.end('HTTP/1.1 500 Internal Server Error\r\n\r\n');
                } else {
                    resOrSocket.status(500).json({ error: `Failed to process request for service "${serviceName}".` });
                }
            },
        })
    );
});

module.exports = router;
