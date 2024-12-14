const ErrorResponseCore = require('./core.error.response');
const  {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class ForbiddenResponse extends ErrorResponseCore {
    constructor(message, code = -1) {
        super(
            message ?? getReasonPhrase(StatusCodes.FORBIDDEN),
            StatusCodes.FORBIDDEN,
            code,
        );
    }
}

module.exports = ForbiddenResponse;