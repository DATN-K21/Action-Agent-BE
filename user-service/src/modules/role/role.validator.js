const validator = require("validator");
const ValidatorConfig = require("../../configs/validator.config");


class RoleValidator extends ValidatorConfig {
    static getRoleAttributes() {
        return ['slug', 'name', 'description', 'grants'];
    }

    static getPermissionGrantAttributes() {
        return ['role', 'resource', 'action', 'attributes'];
    }

    static validateCreateNewRole(req) {
        // Name validation
        if (validator.isEmpty(req.body?.name || '')) {
            return RoleValidator.returnFailedError('Role name is required', 1030101);
        }

        // Description validation
        if (validator.isEmpty(req.body?.description || '')) {
            return RoleValidator.returnFailedError('Role description is required', 1030102);
        }

        // Grants validation
        if (!req.body?.grants) {
            return RoleValidator.returnFailedError('Role grants is required', 1030103);
        } else if (!Array.isArray(req.body?.grants)) {
            return RoleValidator.returnFailedError('Role grants must be an array', 1030104);
        }

        return RoleValidator.returnPassedData({
            userId: req.user.id,
            name: req.body.name,
            description: req.body.description,
            grants: req.body.grants,
        });
    }

    static validateGetRoleList(req) {
        let filter = req.query;
        if (filter) {
            // Limit validation
            if (filter.limit && !validator.isInt(filter.limit)) {
                return RoleValidator.returnFailedError('Limit must be an integer', 1030201);
            }

            // Page validation
            if (filter.page && !validator.isInt(filter.page)) {
                return RoleValidator.returnFailedError('Page must be an integer', 1030202);
            }

            // Sort validation
            if (filter.sort && !validator.isIn(filter.sort, RoleValidator.getRoleAttributes())) {
                return RoleValidator.returnFailedError('Sort name is invalid', 1030203);
            }
            if (filter.sort && filter.sort === 'grants') {
                return RoleValidator.returnFailedError('Sort by grants is not allowed', 1030204);
            }

            // Sort order validation
            if (!filter.sort && filter.sortOrder) {
                return RoleValidator.returnFailedError('Sort order can only be used when sort is given', 1030205);
            } else if (filter.sortOrder && !validator.isIn(filter.sortOrder, [1, -1])) {
                return RoleValidator.returnFailedError('Sort order must be ascending (1) or descending (-1)', 1030206);
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

        return RoleValidator.returnPassedData({
            filter: filter
        });
    }

    static validateGetRoleById(req) {
        // Role ID validation
        if (validator.isEmpty(req.params?.id)) {
            return RoleValidator.returnFailedError('Role ID is required', 1030301);
        } else if (!validator.isMongoId(req.params.id)) {
            return RoleValidator.returnFailedError('Role ID is invalid', 1030302);
        }

        return RoleValidator.returnPassedData({
            roleId: req.params.id
        });
    }

    static validateUpdateRole(req) {
        // Role ID validation
        if (validator.isEmpty(req.params?.id)) {
            return RoleValidator.returnFailedError('Role ID is required', 1030401);
        } else if (!validator.isMongoId(req.params.id)) {
            return RoleValidator.returnFailedError('Role ID is invalid', 1030402);
        }

        // Attribute validation
        const attributes = RoleValidator.getRoleAttributes();
        const hasAttribute = attributes.some((attribute) => req.body[attribute]);
        if (!hasAttribute) {
            return RoleValidator.returnFailedError('No data given to update', 1030403);
        }

        return RoleValidator.returnPassedData({
            roleId: req.params.id,
            slug: req.body?.slug,
            name: req.body?.name,
            description: req.body?.description,
            grants: req.body?.grants,
        });
    }

    static validateDeleteRole(req) {
        // Role ID validation
        if (validator.isEmpty(req.params?.id)) {
            return RoleValidator.returnFailedError('Role ID is required', 1030501);
        } else if (!validator.isMongoId(req.params.id)) {
            return RoleValidator.returnFailedError('Role ID is invalid', 1030502);
        }

        return RoleValidator.returnPassedData({
            roleId: req.params.id
        });
    }

    static validateGetPermissionGrantList(req) {
        let filter = req.query;
        if (filter) {
            // Limit validation
            if (filter.limit && !validator.isInt(filter.limit)) {
                return RoleValidator.returnFailedError('Limit must be an integer', 1030601);
            }

            // Page validation
            if (filter.page && !validator.isInt(filter.page)) {
                return RoleValidator.returnFailedError('Page must be an integer', 1030602);
            }

            // Sort validation
            if (filter.sort && !validator.isIn(filter.sort, RoleValidator.getPermissionGrantAttributes())) {
                return RoleValidator.returnFailedError('Sort name is invalid', 1030603);
            }

            // Sort order validation
            if (!filter.sort && filter.sortOrder) {
                return RoleValidator.returnFailedError('Sort order can only be used when sort is given', 1030604);
            } else if (filter.sortOrder && !validator.isIn(filter.sortOrder, [1, -1])) {
                return RoleValidator.returnFailedError('Sort order must be ascending (1) or descending (-1)', 1030605);
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

        return RoleValidator.returnPassedData({
            filter: filter
        });
    }

    static validateAddNewGrantsToRole(req) {
        // Role ID validation
        if (validator.isEmpty(req.params?.id)) {
            return RoleValidator.returnFailedError('Role ID is required', 1030701);
        } else if (!validator.isMongoId(req.params.id)) {
            return RoleValidator.returnFailedError('Role ID is invalid', 1030702);
        }

        // Grants validation
        if (!req.body?.grant) {
            return RoleValidator.returnFailedError('New grant is required', 1030703);
        } else if (!req.body.grant?.resource || !req.body.grant?.actions || !req.body.grant?.attributes) {
            return RoleValidator.returnFailedError('New grant must have resource, actions, and attributes', 1030704);
        }

        return RoleValidator.returnPassedData({
            roleId: req.params.id,
            newGrant: req.body.grant,
        });
    }

    static validateGetGrantsByRole(req) {
        // Role ID validation
        if (validator.isEmpty(req.params?.id)) {
            return RoleValidator.returnFailedError('Role ID is required', 1030801);
        } else if (!validator.isMongoId(req.params.id)) {
            return RoleValidator.returnFailedError('Role ID is invalid', 1030802);
        }

        return RoleValidator.returnPassedData({
            roleId: req.params.id
        });
    }
}

module.exports = RoleValidator;