const mongoose = require('mongoose');

class MongooseUtil {
    static isMongooseError(error) {
        return error instanceof mongoose.Error;
    }

    static convertToMongooseObjectIdType(id) {
        return new mongoose.Types.ObjectId(id);
    }
}

module.exports = MongooseUtil;
