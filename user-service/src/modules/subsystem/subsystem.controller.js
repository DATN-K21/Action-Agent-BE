const { BadRequestResponse } = require('../../response/error');
const SubSystemValidator = require('./subsystem.validator');
const MongooseUtil = require("../../utils/mongoose.util");
const { OKSuccessResponse } = require('../../response/success');
const SubSystemService = require('./subsystem.service');

class SubSystemController {
    constructor() {
        this.subSystemService = new SubSystemService();
    }
    geSubSystemOwnerIds = async (req, res, next) => {
        const subSystemId = req.params?.id;
        if (!subSystemId) {
            // The request is not for a specific access, so it does not have a specific owner
            return [];
        }
        const foundSubSystem = await this.subSystemService.getSubSystemById(subSystemId);
        return foundSubSystem?.owners?.map(x => x.toString()) ?? [];
    }

    createNewSubSystem = async (req, res) => {
        const validationResult = SubSystemValidator.validateCreateNewSubSystem(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { name, description, owner, logo_url } = validationResult?.data;
        try {
            const result = await this.subSystemService.createNewSubSystem({ name, description, owner, logo_url });
            return new OKSuccessResponse({
                message: 'Create new sub System success',
                data: result,
                code: 1060100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1060106);
            }
            throw error;
        }
    }

    getSubSystemList = async (req, res) => {
        const result = await this.subSystemService.getSubSystemList();
        return new OKSuccessResponse({
            message: 'Get subSystem list success',
            data: result,
            code: 1060200, metadata: {
            }
        }).send(res);
    }

    getSubSystemById = async (req, res) => {
        const validationResult = SubSystemValidator.validateGetSubSystemById(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }
        const { subSystemId } = validationResult?.data;
        try {
            const result = await this.subSystemService.getSubSystemById(subSystemId);
            return new OKSuccessResponse({
                message: 'Get sub system by id success',
                data: result,
                code: 1060300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1060304);
            }
            throw error;
        }
    }

    updateSubSystem = async (req, res) => {
        const validationResult = SubSystemValidator.validateUpdateSubSystem(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { subSystemId, name, description, logo_url, status } = validationResult?.data;
        try {
            const result = await this.subSystemService.updateSubSystem(subSystemId, { name, description, logo_url, status });
            return new OKSuccessResponse({
                message: 'Update sub System success',
                data: result,
                code: 1060400
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1060407);
            }
            throw error;
        }
    }

    deleteSubSystem = async (req, res) => {
        const validationResult = SubSystemValidator.validateDeleteSubSystem(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { subSystemId } = validationResult?.data;
        try {
            const result = await this.subSystemService.deleteSubSystem(subSystemId);
            return new OKSuccessResponse({
                message: 'Delete subSystem success',
                data: {
                    deleted: subSystemId,
                },
                metadata: {
                    code: 1060500,
                    ...result,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1060504);
            }
            throw error;
        }
    }

}

module.exports = new SubSystemController();