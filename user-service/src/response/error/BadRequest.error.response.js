const ErrorResponseCore = require('./core.error.response');
const {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class BadRequestResponse extends ErrorResponseCore {
    constructor(message, code = -1) {
        super(
            message ?? getReasonPhrase(StatusCodes.BAD_REQUEST),
            StatusCodes.BAD_REQUEST,
            code
        );
    }
}

module.exports = BadRequestResponse;