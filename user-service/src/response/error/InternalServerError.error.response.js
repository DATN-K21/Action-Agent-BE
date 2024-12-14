const ErrorResponseCore = require('./core.error.response');
const  {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class InternalServerErrorResponse extends ErrorResponseCore {
    constructor(message, code = -1) {
        super(
            message ?? getReasonPhrase(StatusCodes.INTERNAL_SERVER_ERROR),
            StatusCodes.INTERNAL_SERVER_ERROR,
            code,
        );
    }
}

module.exports = InternalServerErrorResponse;