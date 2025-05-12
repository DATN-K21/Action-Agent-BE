const SuccessResponseCore = require('./core.success.response');

class OKSuccessResponse extends SuccessResponseCore {
    constructor({ message, data, code, metadata }) {
        super({ message, data, code, metadata });
    }

    send(res) {
        return super.send(res);
    }
}

module.exports = OKSuccessResponse;