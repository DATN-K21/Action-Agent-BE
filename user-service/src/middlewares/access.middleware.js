const JWTHelper = require("../helpers/jwt.helper");
const accessModel = require("../modules/access/access.model");
const userModel = require("../modules/user/user.model");
const { UnauthorizedResponse, ConflictResponse, BadRequestResponse } = require("../response/error");

class AccessMiddleware {
    static async checkAccess(req, res, next) {
        const clientId = req.headers['x-client-id'];
        if (!clientId) {
            throw new UnauthorizedResponse('Unauthorized', 1000101);
        }

        const foundUser = await userModel.findById(clientId);
        if (!foundUser) {
            throw new ConflictResponse('User not found', 1000102);
        }
        const foundAccess = await accessModel.findOne({ user_id: foundUser?._id });
        if (!foundAccess) {
            throw new ConflictResponse('User not found', 1000103);
        } else if (!foundAccess.private_key || !foundAccess.public_key) {
            throw new ConflictResponse('Something went wrong', 1000104);
        }

        const token = req.headers['authorization'];
        if (!token) {
            throw new UnauthorizedResponse('Unauthorized', 1000105);
        }
        const tokenParts = token.split(' ');
        if (!tokenParts || tokenParts?.length !== 2 || tokenParts[0] !== 'Bearer') {
            throw new BadRequestResponse('Unauthorized', 1000106);
        }
        const accessToken = token.split(' ')[1];

        try {
            const decodedToken = JWTHelper.verifyToken(accessToken, foundAccess.public_key);
            console.log('decodedToken: ');
            console.log(decodedToken);
            if (!decodedToken) {
                throw new UnauthorizedResponse('Unauthorized', 1000107);
            } else if (!decodedToken?.id || decodedToken?.id !== foundUser._id.toString()) {
                throw new ConflictResponse('User information not match', 1000108);
            }

            req.user = decodedToken;
            req.privateKey = foundAccess.private_key;
            next();
        } catch (error) {
            console.log(error);
            if (JWTHelper.checkIfTokenExpiredError(error)) {
                throw new UnauthorizedResponse('Token is expired', 1000109);
            } else if (JWTHelper.checkIfTokenSignatureError(error)) {
                throw new UnauthorizedResponse('Invalid signature', 10010);
            }
            throw new BadRequestResponse('Something went wrong', 10011);
        }
    }
}

module.exports = AccessMiddleware;