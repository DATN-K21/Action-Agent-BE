const crypto = require('crypto');

const generateRSAKeysForAccess = () => { 
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding: {
            type: 'pkcs1',
            format: 'pem'
        },
        privateKeyEncoding: {
            type: 'pkcs1',
            format: 'pem'
        }
    });
    return { publicKey, privateKey };
}

const generatePEMKeysForAWS = () => { 
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding: {
            type: 'spki',
            format: 'pem'
        },
        privateKeyEncoding: {
            type: 'pkcs8',
            format: 'pem'
        }
    });
    return { publicKey, privateKey };
}

const generateRandomString = (length = 10) => {
    const byteLength = Math.ceil(length / 2);
    return crypto.randomBytes(byteLength).toString('hex').slice(0, length);
}

const generateUUID = () => {
    return crypto.randomUUID();
}

module.exports = {
    generateRSAKeysForAccess,
    generatePEMKeysForAWS,
    generateRandomString,
    generateUUID,
};