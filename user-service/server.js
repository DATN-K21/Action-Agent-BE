const app = require("./src/app");
require('dotenv').config();

const PORT = process.env.PORT || 8100;
const backend_url = process.env.BACKEND_URL || "https://my-ai-agent.azurewebsites.net"

const server = app.listen(PORT, () => {
    console.log(`AI Assistant User Service is listening on port: ${PORT}, url: ${backend_url}:${PORT}`);
})