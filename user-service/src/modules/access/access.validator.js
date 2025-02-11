const validator = require('validator');
const JWTHelper = require('../../helpers/jwt.helper');
const accessModel = require('./access.model');
const MongooseUtil = require('../../utils/mongoose.util');
const userModel = require('../user/user.model');
const ValidatorConfig = require('../../configs/validator.config');

class AccessValidator extends ValidatorConfig {
    static validateSignup(req) {
        // Email validation
        if (validator.isEmpty(req.body?.email || '')) {
            return AccessValidator.returnFailedError('Email is required', 1010101);
        }
        if (!validator.isEmail(req.body?.email)) {
            return AccessValidator.returnFailedError('Invalid email format', 1010102);
        }

        // Password validation
        if (validator.isEmpty(req.body?.password || '')) {
            return AccessValidator.returnFailedError('Password is required', 1010103);
        }

        if (!validator.isLength(req.body?.password, { min: 3 })) {
            return AccessValidator.returnFailedError('Password must be at least 3 characters long', 1010104);
        }

        // Validation passed
        return AccessValidator.returnPassedData({
            email: req.body?.email,
            password: req.body?.password,
        });
    }

    static validateLogin(req) {
        // Email validation
        if (validator.isEmpty(req.body?.email || '')) {
            return AccessValidator.returnFailedError('Email is required', 1010201);
        }
        if (!validator.isEmail(req.body?.email)) {
            return AccessValidator.returnFailedError('Invalid email format', 1010202);
        }

        // Password validation
        if (validator.isEmpty(req.body?.password || '')) {
            return AccessValidator.returnFailedError('Password is required', 1010203);
        }

        if (!validator.isLength(req.body?.password, { min: 3 })) {
            return AccessValidator.returnFailedError('Password must be at least 3 characters long', 1010204);
        }

        // Validation passed
        return AccessValidator.returnPassedData({
            email: req.body?.email,
            password: req.body?.password,
        });
    }

    static validateInvokeNewToken(req) {
        // User ID validation
        if (validator.isEmpty(req.headers['x-client-id'] || '')) {
            return AccessValidator.returnFailedError('Client ID is required', 1010301);
        }

        // Access token validation
        if (validator.isEmpty(req.headers['authorization'] || '')) {
            return AccessValidator.returnFailedError('Authentication credential is required', 1010302);
        }
        const tokenParts = req.headers['authorization'].split(' ');
        if (!tokenParts || tokenParts?.length !== 2 || tokenParts[0] !== 'Bearer') {
            return AccessValidator.returnFailedError('Unauthorized', 1010303);
        }
        const accessToken = tokenParts[1];

        // Refresh token validation
        if (validator.isEmpty(req.body?.refreshToken || '')) {
            return AccessValidator.returnFailedError('Refresh token is required', 1010304);
        }
        const refreshToken = req.body?.refreshToken;

        // Validation passed
        return AccessValidator.returnPassedData({
            userId: req.headers['x-client-id'],
            refreshToken: refreshToken,
            accessToken: accessToken,
        });
    }

    static validateResetPassword(req) {
        // User ID validation
        if (validator.isEmpty(req.headers['x-client-id'] || '')) {
            return AccessValidator.returnFailedError('Client ID is required', 1011401);
        }

        // Access token validation
        if (validator.isEmpty(req.headers['authorization'] || '')) {
            return AccessValidator.returnFailedError('Authentication credential is required', 1011402);
        }
        const tokenParts = req.headers['authorization'].split(' ');
        if (!tokenParts || tokenParts?.length !== 2 || tokenParts[0] !== 'Bearer') {
            return AccessValidator.returnFailedError('Unauthorized', 1011403);
        }
        const resetPasswordToken = tokenParts[1];
        // Password validation
        if (validator.isEmpty(req.body?.newPassword || '')) {
            return AccessValidator.returnFailedError('Password is required', 1011404);
        }

        if (!validator.isLength(req.body?.newPassword, { min: 3 })) {
            return AccessValidator.returnFailedError('Password must be at least 3 characters long', 1011405);
        }

        //Confirm new password validation
        if (validator.isEmpty(req.body?.confirmNewPassword || '')) {
            return AccessValidator.returnFailedError('Confirm password is required', 1011406);
        }
        if (req.body?.newPassword !== req.body?.confirmNewPassword) {
            return AccessValidator.returnFailedError('Password does not match', 1011407);
        }

        // Validation passed
        return AccessValidator.returnPassedData({
            userId: req.headers['x-client-id'],
            resetPasswordToken: resetPasswordToken,
            newPassword: req.body?.newPassword,
        });
    }

    static async validateVerifyEmail(req) {
        if (validator.isEmpty(req.body?.email || '')) {
            return AccessValidator.returnFailedError('Email is required', 1010401);
        }
        if (!validator.isEmail(req.body?.email)) {
            return AccessValidator.returnFailedError('Invalid email format', 1010402);
        }

        // Validation passed
        return AccessValidator.returnPassedData({
            userEmail: req.body?.email
        });
    }

    static async validateVerifyOTP(req) {
        // User identification
        if (validator.isEmpty(req.body?.email || '')) {
            return AccessValidator.returnFailedError('Email is required', 1010501);
        }
        if (!validator.isEmail(req.body?.email)) {
            return AccessValidator.returnFailedError('Invalid email format', 1010502);
        }
        // OTP validation
        if (validator.isEmpty(req.body?.otp || '')) {
            return AccessValidator.returnFailedError('OTP is required', 1010503);
        } else if (!validator.isLength(req.body?.otp, { min: 6, max: 6 })) {
            return AccessValidator.returnFailedError('OTP must be 6 characters long', 1010504);
        }

        // Validation passed
        return AccessValidator.returnPassedData({
            userEmail: req.body?.email,
            otp: req.body?.otp,
        });
    }

    static validateGoogleLogin(req) {
        if (validator.isEmpty(req?.body.id_token || '')) {
            return AccessValidator.returnFailedError('Google ID Token not found', 1010601);
        }
        return AccessValidator.returnPassedData({
            idToken: req.body.id_token,
        });
    }

    static validateFacebookLogin(profile) {
        // Username validation
        if (validator.isEmpty(profile.displayName || '')) {
            return AccessValidator.returnFailedError('Display name not found', 1010903);
        }

        // Facebook ID validation
        if (validator.isEmpty(profile.id || '')) {
            return AccessValidator.returnFailedError('Facebook ID not found', 1010904);
        }

        // Validation passed
        return AccessValidator.returnPassedData({
            username: profile.displayName,
            facebook_id: profile.id,
            type_login: 'facebook'
        });
    }

    static validateLogout(req) {
        // Request user validation
        if (!req.user || !req.user.id) {
            return AccessValidator.returnFailedError('Unauthorized', 1011001);
        }
        // Validation passed
        return AccessValidator.returnPassedData({
            user: req.user,
        });
    }
}

module.exports = AccessValidator;