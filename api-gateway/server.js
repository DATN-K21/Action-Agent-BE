const https = require("https");
const http = require("http");
const app = require("./src/app");
const GENERAL_CONFIGS = require("./src/configs/general.config");
const PORT = GENERAL_CONFIGS.PORT;

if (GENERAL_CONFIGS.ENABLE_HTTPS) {
    // Validate SSL environment variables
    if (!process.env.SSL_KEY_CONTENT || !process.env.SSL_CERT_CONTENT) {
        console.error('ERROR: SSL_KEY_CONTENT and SSL_CERT_CONTENT environment variables are required when HTTPS is enabled');
        process.exit(1);
    }

    // Load your SSL certs from environment variables
    const options = {
        key: Buffer.from(process.env.SSL_KEY_CONTENT, 'base64').toString(),
        cert: Buffer.from(process.env.SSL_CERT_CONTENT, 'base64').toString(),
    };

    // Create HTTPS server
    https.createServer(options, app).listen(PORT, () => {
        console.log(`API Gateway is listening on https://:${PORT}`);
    });
} else {
    // Create HTTP server
    http.createServer(app).listen(PORT, () => {
        console.log(`API Gateway is listening on http://:${PORT}`);
    });
}
