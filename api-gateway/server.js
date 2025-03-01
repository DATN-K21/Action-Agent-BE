const app = require("./src/app");
const GENERAL_CONFIGS = require("./src/configs/general.config");

// Start the Gateway
const PORT = GENERAL_CONFIGS.HTTP_PORT;

// Start the server
app.listen(PORT, () => {
    console.log(`API Gateway running on port ${PORT}`);
});
