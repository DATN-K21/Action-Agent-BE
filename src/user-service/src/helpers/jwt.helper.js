const jwt = require('jsonwebtoken');
const { access_token_expire, refresh_token_expire, reset_password_token_expire, activation_token_expire } = require('../configs/time.config');
require('dotenv').config();
class JWTHelper {
    static generateToken(payload, privateKey, expiresIn) {
        return jwt.sign(payload, privateKey, { expiresIn, algorithm: 'RS256' });
    }

    static generateAccessToken(data, privateKey) {
        return this.generateToken({
            id: data?.id?.toString() ?? data?._id?.toString(),
            email: data?.email,
            username: data?.username,
            role: data?.role?.name,
            isActive: data?.email_verified ? true : false,
        }, privateKey, access_token_expire);
    }

    static generateRefreshToken(data, privateKey) {
        return this.generateToken({
            id: data?.id?.toString() ?? data?._id?.toString(),
            createdAt: new Date(),
        }, privateKey, refresh_token_expire);
    }

    static generateResetPasswordToken(data, privateKey) {
        return this.generateToken({
            userId: data?.id?.toString() ?? data?._id?.toString(),
            purpose: 'reset_password',
        }, privateKey, reset_password_token_expire);
    }

    static generateActivationToken(data, privateKey) {
        return jwt.sign({
            userId: data?.id?.toString() ?? data?._id?.toString(),
            purpose: 'activation',
        }, privateKey, { expiresIn: activation_token_expire, algorithm: 'HS256' });
    }

    static verifyToken(token, publicKey) {
        return jwt.verify(token, publicKey, {
            algorithms: ['RS256']
        });
    }

    static verifyActivationToken(token, publicKey) {
        return jwt.verify(token, publicKey, {
            algorithms: ['HS256']
        });
    }



    static checkIfTokenExpiredError(error) {
        return error instanceof jwt.TokenExpiredError;
    }

    static checkIfTokenSignatureError(error) {
        return error instanceof jwt.JsonWebTokenError && error.message === 'invalid signature';
    }
}

module.exports = JWTHelper;
