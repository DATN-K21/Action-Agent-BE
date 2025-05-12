const { BadRequestResponse } = require('../../response/error');
const ResourceValidator = require('./resource.validator');
const ResourceService = require('./resource.service');
const { CreatedSuccessResponse, OKSuccessResponse } = require('../../response/success');
const MongooseUtil = require('../../utils/mongoose.util');

class ResourceController {
    constructor() {
        this.resourceService = new ResourceService();
    }

    getResourceOwnerIds = async (req, res, next) => {
        const resourceId = req.params?.id;
        if (!resourceId) {
            // The request is not for a specific resource, so it does not have a specific owner
            return [];
        }
        const foundResource = await this.resourceService.getResourceById(resourceId);
        return foundResource?.owners?.map(x => x.toString()) ?? [];
    }

    createNewResource = async (req, res, next) => {
        const validationResult = ResourceValidator.validateCreateNewResource(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { userId, name, description } = validationResult?.data;
        try {
            const result = await this.resourceService.createNewResource(userId, name, description);
            return new CreatedSuccessResponse({
                message: 'Create new resource success',
                data: result,
                code: 1020100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1020104);
            }
            throw error;
        }
    }

    getResourceList = async (req, res, next) => {
        const validationResult = ResourceValidator.validateGetResourceList(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { filter } = validationResult?.data;
        try {
            const result = await this.resourceService.getResourceList(filter);
            return new OKSuccessResponse({
                message: 'Get resource list success',
                data: result,
                code: 1020200,
                metadata: {
                    total: result?.total ?? undefined,
                    page: filter?.page ?? undefined,
                    perpage: filter?.limit ?? undefined,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1020206);
            }
            throw error;
        }
    }

    getResourceById = async (req, res, next) => {
        const validationResult = ResourceValidator.validateGetResourceById(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { resourceId } = validationResult?.data;
        try {
            const result = await this.resourceService.getResourceById(resourceId);
            return new OKSuccessResponse({
                message: 'Get resource by ID success',
                data: result,
                code: 1020300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1020304);
            }
            throw error;
        }
    }

    updateResource = async (req, res, next) => {
        const validationResult = ResourceValidator.validateUpdateResource(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { resourceId, slug, name, description } = validationResult?.data;
        try {
            const result = await this.resourceService.updateResource(resourceId, { slug, name, description });
            return new OKSuccessResponse({
                message: 'Update resource success',
                data: result,
                code: 1020400
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1020405);
            }
            throw error;
        }
    }

    deleteResource = async (req, res, next) => {
        const validationResult = ResourceValidator.validateDeleteResource(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { resourceId } = validationResult?.data;
        try {
            const result = await this.resourceService.deleteResource(resourceId);
            return new OKSuccessResponse({
                message: 'Delete resource success',
                data: {
                    deleted: resourceId,
                },
                code: 1020500,
                metadata: {
                    ...result,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1020504);
            }
            throw error;
        }
    }
}

module.exports = new ResourceController();