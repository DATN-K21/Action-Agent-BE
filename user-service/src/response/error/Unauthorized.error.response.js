const ErrorResponseCore = require('./core.error.response');
const  {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class UnauthorizedResponse extends ErrorResponseCore {
    constructor(message, code = -1) {
        super(
            message ?? getReasonPhrase(StatusCodes.UNAUTHORIZED),
            StatusCodes.UNAUTHORIZED,
            code,
        );
    }
}

module.exports = UnauthorizedResponse;