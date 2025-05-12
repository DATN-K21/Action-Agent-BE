const ErrorResponseCore = require('./core.error.response');
const {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class ConflictResponse extends ErrorResponseCore {
    constructor(message, code = -1) {
        super(
            message ?? getReasonPhrase(StatusCodes.CONFLICT),
            StatusCodes.CONFLICT,
            code
        );
    }
}

module.exports = ConflictResponse;