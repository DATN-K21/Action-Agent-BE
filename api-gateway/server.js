const https = require("https");
const app = require("./src/app");
const GENERAL_CONFIGS = require("./src/configs/general.config");

const PORT = GENERAL_CONFIGS.HTTPS_PORT;

// Load your SSL certs from environment variables
const options = {
    key: Buffer.from(process.env.SSL_KEY_CONTENT, 'base64').toString(),
    cert: Buffer.from(process.env.SSL_CERT_CONTENT, 'base64').toString(),
};

// Create HTTPS server
https.createServer(options, app).listen(PORT, () => {
    console.log(`API Gateway is listening on https://:${PORT}`);
});
