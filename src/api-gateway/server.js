const fs = require("fs");
const https = require("https");
const app = require("./src/app");
const GENERAL_CONFIGS = require("./src/configs/general.config");

const PORT = GENERAL_CONFIGS.HTTPS_PORT;

// Load your SSL certs
const options = {
    key: fs.readFileSync(process.env.SSL_KEY_PATH),
    cert: fs.readFileSync(process.env.SSL_CERT_PATH),
};

// Create HTTPS server
https.createServer(options, app).listen(PORT, () => {
    console.log(`API Gateway is listening on https://:${PORT}`);
});
