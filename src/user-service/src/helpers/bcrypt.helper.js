const bcrypt = require('bcrypt');

class BcryptHelper {
    static async hash(raw) {
        const salt = await bcrypt.genSalt(10);
        return bcrypt.hash(raw, salt);
    }

    static async compare(raw, hashed) {
        return bcrypt.compare(raw, hashed);
    }
}

module.exports = BcryptHelper;
