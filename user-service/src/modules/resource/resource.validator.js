const validator = require('validator');
const ValidatorConfig = require("../../configs/validator.config");

class ResourceValidator extends ValidatorConfig {
    static getResourceAttributes() {
        return ['slug', 'name', 'description'];
    }

    static validateCreateNewResource(req) {
        // Name validation
        if (validator.isEmpty(req.body?.name || '')) {
            return ResourceValidator.returnFailedError('Resource name is required', 1020101);
        }

        // Description validation
        if (validator.isEmpty(req.body?.description || '')) {
            return ResourceValidator.returnFailedError('Resource description is required', 1020102);
        }

        return ResourceValidator.returnPassedData({
            userId: req.user.id,
            name: req.body.name,
            description: req.body.description
        });
    }

    static validateGetResourceList(req) {
        let filter = req.query;
        if (filter) {
            // Limit validation
            if (filter.limit && !validator.isInt(filter.limit)) {
                return ResourceValidator.returnFailedError('Limit must be an integer', 1020201);
            }

            // Page validation
            if (filter.page && !validator.isInt(filter.page)) {
                return ResourceValidator.returnFailedError('Page must be an integer', 1020202);
            }

            // Sort validation
            if (filter.sort && !validator.isIn(filter.sort, ['slug', 'name', 'description'])) {
                return ResourceValidator.returnFailedError('Sort must be slug, name or description', 1020203);
            }


            // Sort order validation

            if (!filter.sort && filter.sortOrder) {
                return ResourceValidator.returnFailedError('Sort order can only be used when sort is given', 1020204);
            } else if (filter.sortOrder && !validator.isIn(filter.sortOrder, [1, -1])) {
                return ResourceValidator.returnFailedError('Sort order must be ascending (1) or descending (-1)', 1020205);
            }

            // Validation passed
            filter = {
                limit: filter?.limit ? parseInt(filter?.limit) : 10,
                page: filter?.page ? parseInt(filter?.page) : 1,
                search: filter?.search,
                sort: filter?.sort,
                sortOrder: filter?.sortOrder ? parseInt(filter?.sortOrder) : 1,
            }
        } else {
            filter = {
                limit: 10,
                page: 1,
                sortOrder: 1,
            }
        }

        return ResourceValidator.returnPassedData({
            filter: filter
        });
    }

    static validateGetResourceById(req) {
        // Resource ID validation
        if (validator.isEmpty(req.params?.id)) {
            return ResourceValidator.returnFailedError('Resource ID is required', 1020301);
        } else if (!validator.isMongoId(req.params.id)) {
            return ResourceValidator.returnFailedError('Resource ID is invalid', 1020302);
        }

        return ResourceValidator.returnPassedData({
            resourceId: req.params.id
        });
    }

    static validateUpdateResource(req) {
        // Resource ID validation
        if (validator.isEmpty(req.params?.id)) {
            return ResourceValidator.returnFailedError('Resource ID is required', 1020401);
        } else if (!validator.isMongoId(req.params.id)) {
            return ResourceValidator.returnFailedError('Resource ID is invalid', 1020402);
        }

        // Attribute validation
        const attributes = ResourceValidator.getResourceAttributes();
        const hasAttribute = attributes.some((attribute) => req.body[attribute]);
        if (!hasAttribute) {
            return ResourceValidator.returnFailedError('No data given to update', 1020403);
        }

        return ResourceValidator.returnPassedData({
            resourceId: req.params.id,
            slug: req.body?.slug,
            name: req.body?.name,
            description: req.body?.description,
        });
    }

    static validateDeleteResource(req) {
        // Resource ID validation
        if (validator.isEmpty(req.params?.id)) {
            return ResourceValidator.returnFailedError('Resource ID is required', 1020501);
        } else if (!validator.isMongoId(req.params.id)) {
            return ResourceValidator.returnFailedError('Resource ID is invalid', 1020502);
        }

        return ResourceValidator.returnPassedData({
            resourceId: req.params.id
        });
    }
}

module.exports = ResourceValidator;