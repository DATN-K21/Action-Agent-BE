const axios = require('axios');

class MyLog {
    constructor({ level, message, context, timestamp, metadata, serviceName }) {
        this.level = level || 'info';
        this.message = message;
        this.context = context || "";
        this.timestamp = timestamp || new Date().toISOString();
        this.metadata = metadata || {};
        this.serviceName = serviceName || "user";
    }
}


class LogHelper {
    constructor() {
        this.logURL = "http://log-service:8101/logs";
    }

    log(logData) {
        return new MyLog(logData);
    }

    pushLog = async (req, res, next) => {
        const level = "info";
        const message = req.body?.message ?? "User request";
        const metadata = req.body;
        const context = req.path;

        const myLog = this.log({ level, message, context, metadata });
        console.log("My log:");
        console.log(myLog);
        try {
            const response = await axios.post(this.logURL, myLog, { timeout: 5000 });
            if (!response || !response?.data) {
                throw new Error("Error pushing log with no response nor data!");
            }

            return res.status(200).json({
                message: "Log pushed successfully",
                data: response.data,
            });
        } catch (error) {
            console.log("Error pushing log: ", error.message);
            // Send error response to the client
            return res.status(500).json({
                message: "Failed to push log",
                error: error.message,
            });
        }
    }
}

module.exports = new LogHelper();