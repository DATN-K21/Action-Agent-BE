const ErrorResponseCore = require('./core.error.response');
const  {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class NotFoundResponse extends ErrorResponseCore {
    constructor(message, code = -1) {
        super(
            message ?? getReasonPhrase(StatusCodes.NOT_FOUND),
            StatusCodes.NOT_FOUND,
            code,
        );
    }
}

module.exports = NotFoundResponse;