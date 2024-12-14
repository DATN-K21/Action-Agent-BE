const SuccessResponseCore = require('./core.success.response');
const {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class CreatedSuccessResponse extends SuccessResponseCore {
    constructor({ message, data, code, metadata }) {
        super({ message, data, code, metadata, statusCode: StatusCodes.CREATED, reason: getReasonPhrase(StatusCodes.CREATED) });
    }

    send(res) {
        return super.send(res);
    }
}

module.exports = CreatedSuccessResponse;