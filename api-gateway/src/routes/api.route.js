const router = require('express').Router();
const { createProxyMiddleware, fixRequestBody } = require('http-proxy-middleware');
const ENDPOINT_CONFIGS = require('../configs/endpoint.config');
const currentUserMiddleware = require('../middlewares/currentUser.middleware');
const TIME_CONFIGS = require('../configs/time.config');
const privateEndpointMiddleware = require('../middlewares/privateEndpoint.middleware');

const serviceRegistry = {
    'user': ENDPOINT_CONFIGS.USER_SERVICE_URL,
    'ai': ENDPOINT_CONFIGS.AI_SERVICE_URL,
    'extension:': ENDPOINT_CONFIGS.EXTENSION_SERVICE_URL,
    'voice': ENDPOINT_CONFIGS.VOICE_SERVICE_URL
};

Object.entries(serviceRegistry).forEach(([serviceName, target]) => {
    router.use(privateEndpointMiddleware);
    router.use(currentUserMiddleware);

    router.use(`/${serviceName}/*`,
        createProxyMiddleware({
            target,
            changeOrigin: true, // Adjust the host header to match the target
            ws: true, // Proxy websockets
            pathRewrite: (path, req) => {
                const isWs = req.headers.upgrade && req.headers.upgrade.toLowerCase() === 'websocket';
                let originalPath = isWs ? (req.url || path) : (req.originalUrl || path);
                const rewrittenPath = originalPath.replace(new RegExp(`/${serviceName}`), '');
                console.log("[HTTP] Rewritten path:", rewrittenPath);
                return rewrittenPath;
            },
            logLevel: 'debug', // Enable debug-level logging in the proxy
            timeout: TIME_CONFIGS.MICROSERVICE_TIMEOUT,
            proxyTimeout: TIME_CONFIGS.MICROSERVICE_TIMEOUT,
            on: {
                proxyReq: fixRequestBody,
            },
            onError(err, req, resOrSocket) {
                console.error(`Proxy error for service '${serviceName}':`, err.message);
                const isWs = req.headers.upgrade && req.headers.upgrade.toLowerCase() === 'websocket';

                if (isWs) {
                    resOrSocket.end('HTTP/1.1 500 Internal Server Error\r\n\r\n');
                } else {
                    resOrSocket.status(err?.status || 500).json({
                        status: err?.status || 500,
                        error: errorMessage || 'Internal Server Error',
                        code: err?.code,
                    });
                }
            },
        })
    );
});

module.exports = router;
