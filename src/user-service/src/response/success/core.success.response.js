const {
    StatusCodes,
    getReasonPhrase,
} = require('http-status-codes');

class SuccessResponseCore {
    constructor({ message, data, code, metadata = {}, statusCode = StatusCodes.OK, reason = getReasonPhrase(StatusCodes.OK) }) {
        this.status = statusCode;
        this.message = message ?? reason;
        this.code = code;
        this.data = data;
        this.metadata = metadata;
    }

    send(res) {
        return res.status(this.status ?? StatusCodes.OK).json(this);
    }
}

module.exports = SuccessResponseCore;