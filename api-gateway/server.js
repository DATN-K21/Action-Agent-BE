const https = require("https");
const app = require("./src/app");
const GENERAL_CONFIGS = require("./src/configs/general.config");

const PORT = GENERAL_CONFIGS.HTTPS_PORT;

// Load your SSL certs from environment variables
const options = {
    key: process.env.SSL_KEY_CONTENT,
    cert: process.env.SSL_CERT_CONTENT,
};

// Create HTTPS server
https.createServer(options, app).listen(PORT, () => {
    console.log(`API Gateway is listening on https://:${PORT}`);
});
