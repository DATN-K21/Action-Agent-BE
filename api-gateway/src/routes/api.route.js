const router = require('express').Router();
const { createProxyMiddleware, fixRequestBody } = require('http-proxy-middleware');
const axios = require('axios');

const serviceRegistry = {
    'user': 'http://user-service:8100',
    'log': 'http://log-service:8101',
};

// router.post('/user/api/v1/log', async (req, res) => {
//     try {
//         console.log('[DEBUG] Forwarding request to user-service');
//         console.log('[DEBUG] Request body:', req.body);
//         console.log('[DEBUG] Request headers:', req.headers);
//         "http://log-service:8101/logs"

//         const response = await axios.post('http://user-service:8100/api/v1/log', req.body, {
//             headers: {
//                 ...req.headers,
//                 'Content-Type': 'application/json',
//             },
//             timeout: 15000,
//         });
//         console.log('[DEBUG] Response from user-service:', response.data);

//         return res.status(200).json({ message: 'Log created successfully', data: response.data });

//     } catch (error) {
//         console.error('[DEBUG] Forwarding error:', error.message);
//         console.error('[DEBUG] Error response:', error.response?.data || error.message);

//         return res.status(error.response?.status || 500).send(error.response?.data || { error: 'Internal Server Error' });
//     }

// });


router.use((req, res, next) => {
    console.log(`[DEBUG] Incoming request: ${req.method} - ${req.originalUrl}`);
    next();
});

Object.entries(serviceRegistry).forEach(([serviceName, target]) => {
    router.use(`/${serviceName}/*`, (req, res, next) => {
        console.log(`[DEBUG] Forwarding request to '${serviceName}' service`);
        console.log(`  Target: ${target}`);
        console.log(`  Path: ${req.originalUrl}`);
        console.log(`  Method: ${req.method}`);
        console.log(`  Headers: ${JSON.stringify(req.headers)}`);
        console.log(`  Body: ${JSON.stringify(req.body)}`);
        next();
    });

    router.use(`/${serviceName}/*`,
        createProxyMiddleware({
            target,
            changeOrigin: true, // Adjust the host header to match the target
            // pathRewrite: {
            //     [`^/api/${serviceName}`]: '', // Remove the service prefix from the path
            // },
            pathRewrite: (path, req) => {
                console.log(`[DEBUG] Rewriting path for '${serviceName}': ${req.originalUrl}`);
                const newPath = req.originalUrl;
                // Remove `/api/${serviceName}` from the path
                const rewrittenPath = newPath.replace(new RegExp(`^/api/${serviceName}`), '');
                console.log(`[DEBUG] Rewritten path: ${rewrittenPath}`);
                return rewrittenPath;
            },
            logLevel: 'debug', // Enable debug-level logging in the proxy
            timeout: 5000, // 5 seconds
            proxyTimeout: 5000, // 5 seconds
            // onProxyReq(proxyReq, req, res) {
            //     Object.entries(req.headers).forEach(([key, value]) => {
            //         proxyReq.setHeader(key, value);
            //     });

            //     // Forward request body if present
            //     if (req.body) {
            //         const bodyData = JSON.stringify(req.body);
            //         proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
            //         proxyReq.setHeader('Content-Type', 'application/json');
            //         proxyReq.write(bodyData);

            //         proxyReq.end();
            //     }

            //     console.log(`[DEBUG] Proxying request:`);
            //     console.log(`  Target: ${target}`);
            //     console.log(`  Service: ${serviceName}`);
            //     console.log(`  Path: ${req.originalUrl}`);
            //     console.log(`  Method: ${req.method}`);
            //     console.log(`  Headers: ${JSON.stringify(req.headers)}`);
            // },
            on: {
                proxyReq: fixRequestBody,
                proxyRes(proxyRes, req, res) {
                    console.log(`[DEBUG] Response from target:`);
                    console.log(`  Status Code: ${proxyRes.statusCode}`);
                    console.log(`  Target: ${target}`);
                    console.log(`  Service: ${serviceName}`);

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

// router.use('/:serviceName/*', (req, res, next) => {
//     const { serviceName } = req.params;
//     const target = serviceRegistry[serviceName];

//     if (!target) {
//         return res.status(404).json({ error: `Service '${serviceName}' not found.` });
//     }

//     // Dynamically forward the request to the target service
//     createProxyMiddleware({
//         target,
//         changeOrigin: true, // Adjust the host header to match the target
//         pathRewrite: {
//             [`^/api/${serviceName}`]: '', // Remove the service prefix from the path
//         },
//         onError(err, req, res) {
//             console.error(`Proxy error: ${err.message}`);
//             res.status(500).json({ error: 'Failed to process request.' });
//         },
//         timeout: 5000, // 5 seconds
//         onProxyReq(proxyReq, req, res) {
//             res.setTimeout(5000, () => {
//                 proxyReq.abort();
//                 res.status(504).json({ error: 'Gateway timeout' });
//             });
//         },
//     })(req, res, next);
// });

module.exports = router;
