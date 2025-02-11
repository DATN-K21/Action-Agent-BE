const app = require("./src/app");

// Start the Gateway
const PORT = process.env.PORT || 8000;

// Start the server
app.listen(PORT, () => {
    console.log(`API Gateway running on port ${PORT}`);
});
