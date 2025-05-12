const ValidatorConfig = require("../../configs/validator.config");
const validator = require("validator");
class SubSystemValidator extends ValidatorConfig {

    static getSubSystemAttributes() {
        return ['name', 'description', 'owner', 'logo_url', 'status'];
    }

    static validateCreateNewSubSystem(req) {
        const body = req.body;

        if (validator.isEmpty(body.name ?? "")) {
            return SubSystemValidator.returnFailedError('SubSystem Name is required', 1060101);
        }

        if (validator.isEmpty(body.description ?? "")) {
            return SubSystemValidator.returnFailedError('SubSystem Description is required', 1060102);
        }

        if (validator.isEmpty(body.logo_url ?? "")) {
            return SubSystemValidator.returnFailedError('Logo URL is required', 1060103);
        } else if (!validator.isURL(body.logo_url)) {
            return SubSystemValidator.returnFailedError('Logo URL is invalid', 1040104);
        }

        return SubSystemValidator.returnPassedData({
            name: body.name,
            description: body.description,
            owner: req.user.id,
            logo_url: body.logo_url,
        });
    }

    static validateGetSubSystemList(req) {
        let filter = req.query;
        if (filter) {
            if (filter.limit && !validator.isInt(filter.limit)) {
                return SubSystemValidator.returnFailedError('Limit must be an integer', 1060201);
            }

            if (filter.page && !validator.isInt(filter.page)) {
                return SubSystemValidator.returnFailedError('Page must be an integer', 1060202);
            }
        }

        return SubSystemValidator.returnPassedData({
            filter: {
                limit: parseInt(filter.limit) ?? 10,
                page: parseInt(filter.page) ?? 1,
            }
        });
    }
    static validateGetSubSystemById(req) {
        const subSystemId = req.params?.id;
        if (!subSystemId) {
            return SubSystemValidator.returnFailedError('SubSystem ID is required', 1060301);
        } else if (!validator.isMongoId(subSystemId)) {
            return SubSystemValidator.returnFailedError('SubSystem ID is invalid', 1060302);
        }

        return SubSystemValidator.returnPassedData({
            subSystemId: subSystemId
        });
    }
    static validateUpdateSubSystem(req) {
        const subSystemId = req.params.id;
        if (!subSystemId) {
            return SubSystemValidator.returnFailedError('SubSystem ID is required', 1060401);
        }
        else if (!validator.isMongoId(subSystemId)) {
            return SubSystemValidator.returnFailedError('SubSystem ID is invalid', 1060402);
        }
        const attributes = SubSystemValidator.getSubSystemAttributes();
        const hasAttributes = attributes.some((attribute) => req.body[attribute]);
        if (!hasAttributes) {
            return SubSystemValidator.returnFailedError('At least one attribute is required', 1060403);
        }
        const body = req.body;
        if (body.logo_url && !validator.isURL(body.logo_url)) {
            return SubSystemValidator.returnFailedError('Logo URL is invalid', 1060404);
        }
        if (body.status && !['active', 'inactive', 'blocked', 'maintaining'].includes(body.status)) {
            return SubSystemValidator.returnFailedError('Status is invalid', 1060405);
        }
        return SubSystemValidator.returnPassedData({
            subSystemId: subSystemId,
            name: body.name ?? undefined,
            description: body.description ?? undefined,
            logo_url: body.logo_url ?? undefined,
            status: body.status ?? undefined
        });

    }
    static validateDeleteSubSystem(req) {
        const subSystemId = req.params.id;
        if (!subSystemId) {
            return SubSystemValidator.returnFailedError('SubSystem ID is required', 1060501);
        } else if (!validator.isMongoId(subSystemId)) {
            return SubSystemValidator.returnFailedError('SubSystem ID is invalid', 1060502);
        }
        return SubSystemValidator.returnPassedData({
            subSystemId: subSystemId
        });
    }
}

module.exports = SubSystemValidator;