const { BadRequestResponse } = require("../../response/error");
const { OKSuccessResponse, CreatedSuccessResponse } = require("../../response/success");
const MongooseUtil = require("../../utils/mongoose.util");
const UserService = require("./user.service");
const UserValidator = require("./user.validator");

class UserController {
    constructor() {
        this.userService = new UserService();
    }

    getUserOwnerIds = async (req) => {
        const userId = req.params?.id;
        if (!userId) {
            // The request is not for a specific user, so it does not have a specific owner
            return [];
        }
        const foundUser = await this.userService.getUserById(userId);
        return foundUser?.owners?.map(x => x.toString()) ?? [];
    };

    createNewUser = async (req, res, next) => {
        const validationResult = UserValidator.validateCreateNewUser(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { username, email, password, fullname, email_verified, avatar } = validationResult?.data;
        try {
            const result = await this.userService.createNewUser({ username, email, password, fullname, email_verified, avatar });
            return new CreatedSuccessResponse({
                message: 'Create new user success',
                data: result,
                code: 1040100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1040110);
            }
            throw error;
        }
    }

    getUserList = async (req, res, next) => {
        const validationResult = UserValidator.validateGetUserList(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { filter } = validationResult?.data;
        try {
            const result = await this.userService.getUserList(filter);
            return new OKSuccessResponse({
                message: 'Get user list success',
                data: result.data,
                code: 1040200,
                metadata: {
                    total: result?.total ?? undefined,
                    page: filter?.page ?? undefined,
                    perpage: filter?.limit ?? undefined,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1040206);
            }
            throw error;
        }
    }

    getUserById = async (req, res, next) => {
        const validationResult = UserValidator.validateGetUserById(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { userId } = validationResult?.data;
        try {
            const result = await this.userService.getUserById(userId);
            return new OKSuccessResponse({
                message: 'Get user by ID success',
                data: result,
                code: 1040300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1040305);
            }
            throw error;
        }
    }

    updateUser = async (req, res, next) => {
        const validationResult = UserValidator.validateUpdateUser(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { userId, username, password, fullname, role, email_verified, avatar, slug } = validationResult?.data;
        try {
            const result = await this.userService.updateUser(userId, { username, password, fullname, role, email_verified, avatar, slug });
            return new OKSuccessResponse({
                message: 'Update user success',
                data: result,
                code: 1040400
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1040410);
            }
            throw error;
        }
    }

    deleteUser = async (req, res, next) => {
        const validationResult = UserValidator.validateDeleteUser(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { userId } = validationResult?.data;
        try {
            const result = await this.userService.deleteUser(userId);
            return new OKSuccessResponse({
                message: 'Delete user success',
                data: {
                    deleted: userId,
                },
                code: 1040500,
                metadata: {
                    ...result,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1040504);
            }
            throw error;
        }
    }
}

module.exports = new UserController();