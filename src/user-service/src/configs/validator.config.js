
class ValidatorConfig {
    static returnFailedError(message, code) {
        return {
            error: true,
            message: message,
            code: code,
        };
    }

    static returnPassedData(data) {
        return {
            error: false,
            data: data,
        };
    }
}

module.exports = ValidatorConfig;