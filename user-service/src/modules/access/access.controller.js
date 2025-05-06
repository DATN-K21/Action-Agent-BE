const AccessService = require("./access.service");
const { OKSuccessResponse, CreatedSuccessResponse } = require('../../response/success');
const { BadRequestResponse } = require('../../response/error');
const AccessValidator = require("./access.validator");
const MongooseUtil = require("../../utils/mongoose.util");
const { syncData } = require("../../helpers/sync.helper");
require('dotenv').config();

class AccessController {
    constructor() {
        this.accessService = new AccessService();
    }

    getAccessOwnerIds = async (req, res, next) => {
        const accessId = req.params?.id;
        if (!accessId) {
            // The request is not for a specific access, so it does not have a specific owner
            return [];
        }
        const foundAccess = await this.accessService.getAccessById(accessId);
        return foundAccess?.owners?.map(x => x.toString()) ?? [];
    }

    handleSignup = async (req, res, next) => {
        const validationResult = AccessValidator.validateSignup(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { email, password, username, firstName, lastName } = validationResult?.data;
        try {
            const result = await this.accessService.handleSignup(email, password, username, firstName, lastName);
            //Sync signup data with ai-service
            const userInfo = {
                id: result.id,
                email: email,
                username: username,
                firstName: firstName,
                lastName: lastName
            }
            let response = await syncData('/private/user/create', userInfo);
            if (response.error) {
                throw new BadRequestResponse("Something went sync data", 1010107);
            }

            return new CreatedSuccessResponse({
                message: 'Signup success',
                data: result,
                code: 1010100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1010106);
            }
            throw error;
        }
    }

    handleLogin = async (req, res, next) => {
        const validationResult = AccessValidator.validateLogin(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { email, password } = validationResult?.data;
        try {
            const result = await this.accessService.handleLogin(email, password);
            return new OKSuccessResponse({
                message: 'Login success',
                data: result,
                code: 1010200,
                metadata: {
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1010209);
            }
            throw error;
        }
    }

    handleInvokeNewTokens = async (req, res, next) => {
        const validationResult = AccessValidator.validateInvokeNewToken(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { userId, accessToken, refreshToken } = validationResult?.data;
        try {
            const result = await this.accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
            return new OKSuccessResponse({
                message: 'Invoke new tokens success',
                data: result,
                code: 1010300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1010315);
            }
            throw error;
        }
    }

    // handleVerifyEmail = async (req, res, next) => {
    //     const validationResult = AccessValidator.validateVerifyEmail(req);
    //     if (validationResult?.error === true) {
    //         throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
    //     }
    //     const { userEmail } = validationResult?.data;

    //     try {
    //         await this.accessService.sendOTPToVerifyEmail(userEmail);
    //         return new OKSuccessResponse({
    //             message: 'Send email to user email success',
    //             data: {
    //                 email: userEmail
    //             },
    //             code: 1010400
    //         }).send(res);
    //     } catch (error) {
    //         if (MongooseUtil.isMongooseError(error)) {
    //             throw new BadRequestResponse("Something went wrong", 1010408);
    //         }
    //         throw error;
    //     }
    // }

    // handleVerifyOTP = async (req, res, next) => {
    //     const validationResult = AccessValidator.validateVerifyOTP(req);
    //     if (validationResult?.error === true) {
    //         throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
    //     }

    //     const { userEmail, otp } = validationResult?.data;
    //     try {
    //         const response = await this.accessService.verifyOTP(userEmail, otp);
    //         return new OKSuccessResponse({
    //             message: 'Verify OTP success',
    //             data: response,
    //             code: 1010500
    //         }).send(res);
    //     } catch (error) {
    //         if (MongooseUtil.isMongooseError(error)) {
    //             throw new BadRequestResponse("Something went wrong", 1010511);
    //         }
    //         throw error;
    //     }
    // }

    handleLoginWithGoogle = async (req, res, next) => {
        const validationResult = AccessValidator.validateGoogleLogin(req);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }

        const { idToken } = validationResult.data;
        try {
            const result = await this.accessService.loginWithGoogle(idToken);

            return new OKSuccessResponse({
                message: 'Login with google success',
                data: result,
                code: 1010600
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1010606);
            }
            throw error;
        }
    }

    handleLoginWithFacebook = async (req, res, next) => {
        const profile = req.user;
        const validationResult = AccessValidator.validateFacebookLogin(profile);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }

        const dataRaw = validationResult.data;

        try {
            const result = await this.accessService.loginWithFacebook(dataRaw);
            return new OKSuccessResponse({
                message: 'Login with facebook success',
                data: result,
                code: 1010900
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1010905);
            }
            throw error;
        }
    }

    handleLogout = async (req, res, next) => {
        const validationResult = AccessValidator.validateLogout(req);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }

        const { user } = validationResult.data;

        try {
            await this.accessService.handleLogout(user);
            return new OKSuccessResponse({
                message: 'Logout success',
                data: {},
                metadata: {
                    code: 1011000,
                    userId: user.id,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1011001);
            }
            throw error;
        }
    }

    handleSendOTPToResetPassword = async (req, res, next) => {
        const validationResult = AccessValidator.validateVerifyEmail(req);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }
        const { userEmail } = validationResult?.data;
        try {
            await this.accessService.sendOTPToResetPassword(userEmail);
            return new OKSuccessResponse({
                message: 'Send OTP to reset password success',
                data: {
                    email: userEmail
                },
                code: 1011200
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1011209);
            }
            throw error;
        }
    }

    handleSendLinkToActivateAccount = async (req, res, next) => {
        const validationResult = AccessValidator.validateVerifyEmail(req);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }
        const { userEmail } = validationResult?.data;
        try {
            await this.accessService.sendLinkToActivateAccount(userEmail);
            return new OKSuccessResponse({
                message: 'Send link to activate account success',
                data: {
                    email: userEmail
                },
                code: 1011100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1011109);
            }
            throw error;
        }
    }

    handleActivateAccount = async (req, res, next) => {

        const validationResult = AccessValidator.validateActivateAccount(req);

        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }

        const { activationToken } = validationResult?.data;

        try {
            const result = await this.accessService.activateAccount(activationToken);
            return new OKSuccessResponse({
                message: 'Activate account success',
                data: result,
                code: 1011300
            }).send(res);

        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1011215);
            }
            throw error;
        }
    }

    handleConfirmOTPToResetPassword = async (req, res, next) => {
        const validationResult = AccessValidator.validateVerifyOTP(req);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }
        const { userEmail, otp } = validationResult?.data;
        try {
            const result = await this.accessService.confirmOTPToResetPassword(userEmail, otp);
            return new OKSuccessResponse({
                message: 'Confirm OTP to reset password success',
                data: result,
                code: 1011300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1011311);
            }
            throw error;
        }
    }

    handleResetPassword = async (req, res, next) => {
        const validationResult = AccessValidator.validateResetPassword(req);
        if (validationResult.error) {
            throw new BadRequestResponse(validationResult.message, validationResult.code);
        }
        const { userId, resetPasswordToken, newPassword } = validationResult?.data;
        try {
            const result = await this.accessService.resetPassword(userId, resetPasswordToken, newPassword);
            return new OKSuccessResponse({
                message: 'Reset password success',
                data: result,
                code: 1011400
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1011415);
            }
            throw error;
        }
    }
}
module.exports = new AccessController();
