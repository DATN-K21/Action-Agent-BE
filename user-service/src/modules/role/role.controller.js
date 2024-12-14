const { BadRequestResponse } = require("../../response/error");
const { CreatedSuccessResponse, OKSuccessResponse } = require("../../response/success");
const MongooseUtil = require("../../utils/mongoose.util");
const RoleService = require("./role.service");
const RoleValidator = require("./role.validator");


class RoleController {
    constructor() {
        this.roleService = new RoleService();
    }

    getRoleOwnerIds = async (req, res, next) => {
        const roleId = req.params?.id;
        if (!roleId) {
            // The request is not for a specific role, so it does not have a specific owner
            return [];
        }
        const foundRole = await this.roleService.getRoleById(roleId);
        return foundRole?.owners?.map(x => x.toString()) ?? [];
    }

    createNewRole = async (req, res, next) => {
        const validationResult = RoleValidator.validateCreateNewRole(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { userId, name, description, grants } = validationResult?.data;
        try {
            const result = await this.roleService.createNewRole(userId, name, description, grants);
            return new CreatedSuccessResponse({
                message: 'Create new role success',
                data: result,
                code: 1030100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030106);
            }
            throw error;
        }
    }

    getRoleList = async (req, res, next) => {
        const validationResult = RoleValidator.validateGetRoleList(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { filter } = validationResult?.data;
        try {
            const result = await this.roleService.getRoleList(filter);
            return new OKSuccessResponse({
                message: 'Get role list success',
                data: result.data,
                code: 1030200,
                metadata: {
                    total: result?.total ?? undefined,
                    page: filter?.page ?? undefined,
                    perpage: filter?.limit ?? undefined,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030207);
            }
            throw error;
        }
    }

    getRoleById = async (req, res, next) => {
        const validationResult = RoleValidator.validateGetRoleById(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { roleId } = validationResult?.data;
        try {
            const result = await this.roleService.getRoleById(roleId);
            return new OKSuccessResponse({
                message: 'Get role by ID success',
                data: result,
                code: 1030300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030304);
            }
            throw error;
        }
    }

    updateRole = async (req, res, next) => {
        const validationResult = RoleValidator.validateUpdateRole(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { roleId, slug, name, description, grants } = validationResult?.data;
        try {
            const result = await this.roleService.updateRole(roleId, { slug, name, description, grants });
            return new OKSuccessResponse({
                message: 'Update role success',
                data: result,
                code: 1030400
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030405);
            }
            throw error;
        }
    }

    deleteRole = async (req, res, next) => {
        const validationResult = RoleValidator.validateDeleteRole(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { roleId } = validationResult?.data;
        try {
            const result = await this.roleService.deleteRole(roleId);
            return new OKSuccessResponse({
                message: 'Delete role success',
                data: {
                    deleted: roleId,
                },
                code: 1030500,
                metadata: {
                    ...result,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030504);
            }
            throw error;
        }
    }

    getPermissionGrantList = async (req, res, next) => {
        const validationResult = RoleValidator.validateGetPermissionGrantList(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { filter } = validationResult?.data;
        try {
            const result = await this.roleService.getPermissionGrantList(filter);
            return new OKSuccessResponse({
                message: 'Get permission grant list success',
                data: result.data,
                code: 1030600,
                metadata: {
                    total: result?.total ?? undefined,
                    page: filter?.page ?? undefined,
                    perpage: filter?.limit ?? undefined,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030606);
            }
            throw error;
        }
    }

    addNewGrantsToRole = async (req, res, next) => {
        const validationResult = RoleValidator.validateAddNewGrantsToRole(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { roleId, newGrant } = validationResult?.data;
        try {
            const result = await this.roleService.addNewGrantsToRole(roleId, newGrant);
            return new OKSuccessResponse({
                message: 'Add new grants to role success',
                data: result,
                code: 1030700
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030706);
            }
            throw error;
        }
    }

    getGrantsByRole = async (req, res, next) => {
        const validationResult = RoleValidator.validateGetGrantsByRole(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { roleId } = validationResult?.data;
        try {
            const result = await this.roleService.getGrantsByRole(roleId);
            return new OKSuccessResponse({
                message: 'Get grants by role success',
                data: result,
                code: 1030800
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1030804);
            }
            throw error;
        }
    }
}

module.exports = new RoleController();