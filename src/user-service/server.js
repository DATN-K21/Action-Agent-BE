const app = require("./src/app");
require('dotenv').config();

const PORT = process.env.PORT || 15100;

const server = app.listen(PORT, () => {
    console.log(`User Service is listening on http://:${PORT}`);
})