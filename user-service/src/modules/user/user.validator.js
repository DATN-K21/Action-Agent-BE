const ValidatorConfig = require("../../configs/validator.config");
const validator = require("validator");

class UserValidator extends ValidatorConfig {
    static getUserAttributes() {
        return ['slug', 'email', 'password', 'username', 'fullname', 'avatar', 'role', 'email_verified', 'type_login', 'google_id', 'facebook_id'];
    }

    static getUserScopes() {
        return ['basic', 'detail'];
    }

    static validateCreateNewUser(req) {
        const body = req.body;
        // Email validation
        if (validator.isEmpty(body.email ?? "")) {
            return UserValidator.returnFailedError('Email is required', 1040101);
        } else if (!validator.isEmail(body.email)) {
            return UserValidator.returnFailedError('Email is invalid', 1040102);
        }

        // Password validation
        if (validator.isEmpty(body.password ?? "")) {
            return UserValidator.returnFailedError('Password is required', 1040103);
        } else if (!validator.isLength(body.password, { min: 3 })) {
            return UserValidator.returnFailedError('Password must be at least 3 characters long', 1040104);
        }

        // Role validation
        if (validator.isEmpty(body.roleId ?? "")) {
            return UserValidator.returnFailedError('Role ID is required', 1040105);
        } else if (!validator.isMongoId(body.roleId)) {
            return UserValidator.returnFailedError('Role ID is invalid', 1040106);
        }

        // Email verification validation
        let emailVerified = body.email_verified;
        if (validator.isEmpty(emailVerified ?? "")) {
            emailVerified = false;
        } else if (!validator.isBoolean(body.email_verified)) {
            return UserValidator.returnFailedError('Email verification must be a boolean', 1040107);
        }

        // Validation passed
        return UserValidator.returnPassedData({
            email: body.email,
            password: body.password,
            role: body.roleId,
            email_verified: emailVerified,
            username: body.username ?? "",
            fullname: body.fullname ?? "",
            avatar: body.avatar ?? "",
        });
    }

    static validateGetUserList(req) {
        let filter = req.query;
        if (filter) {
            // Limit validation
            if (filter.limit && !validator.isInt(filter.limit)) {
                return UserValidator.returnFailedError('Limit must be an integer', 1040201);
            }

            // Page validation
            if (filter.page && !validator.isInt(filter.page)) {
                return UserValidator.returnFailedError('Page must be an integer', 1040202);
            }

            // Sort validation
            if (filter.sort && !validator.isIn(filter.sort, UserValidator.getUserAttributes())) {
                return UserValidator.returnFailedError('Sorted attribute is invalid', 1040203);
            }


            // Sort order validation
            if (!filter.sort && filter.sortOrder) {
                return UserValidator.returnFailedError('Sort order can only be used when sort is given', 1040204);
            } else if (filter.sortOrder && !validator.isIn(filter.sortOrder, [1, -1])) {
                return UserValidator.returnFailedError('Sort order must be ascending (1) or descending (-1)', 1040205);
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

        return UserValidator.returnPassedData({
            filter: filter
        });
    }


    static validateGetUserById(req) {
        const userId = req.params?.id;
        if (!userId) {
            return UserValidator.returnFailedError('User ID is required', 1040301);
        } else if (!validator.isMongoId(userId)) {
            return UserValidator.returnFailedError('User ID is invalid', 1040302);
        }

        // Validation passed
        return UserValidator.returnPassedData({
            userId: userId,
        });
    }

    static validateUpdateUser(req) {
        const userId = req.params?.id;
        if (!userId) {
            return UserValidator.returnFailedError('User ID is required', 1040401);
        } else if (!validator.isMongoId(userId)) {
            return UserValidator.returnFailedError('User ID is invalid', 1040402);
        }

        // Attribute validation
        const attributes = UserValidator.getUserAttributes();
        const hasAttribute = attributes.some((attribute) => req.body[attribute]);
        if (!hasAttribute) {
            return UserValidator.returnFailedError('No data given to update', 1040403);
        }

        const body = req.body;
        // Email validation
        if (body.email) {
            return UserValidator.returnFailedError('Email is irreplaceable', 1040404);
        }

        // Password validation
        if (body.password && !validator.isLength(body.password, { min: 3 })) {
            return UserValidator.returnFailedError('Password must be at least 3 characters long', 1040405);
        }

        // Role validation
        if (body.roleId && !validator.isMongoId(body.roleId)) {
            return UserValidator.returnFailedError('Role ID is invalid', 1040406);
        }

        // Email verification validation
        if (body.email_verified && !validator.isBoolean(body.email_verified)) {
            return UserValidator.returnFailedError('Email verification must be a boolean', 1040407);
        }

        // Validation passed
        return UserValidator.returnPassedData({
            userId: userId,
            password: body.password ?? undefined,
            role: body.roleId ?? undefined,
            email_verified: body.email_verified ?? undefined,
            username: body.username ?? undefined,
            fullname: body.fullname ?? undefined,
            avatar: body.avatar ?? undefined,
            slug: body.slug ?? undefined,
        });
    }

    static validateDeleteUser(req) {
        const userId = req.params?.id;
        if (!userId) {
            return UserValidator.returnFailedError('User ID is required', 1040501);
        } else if (!validator.isMongoId(userId)) {
            return UserValidator.returnFailedError('User ID is invalid', 1040502);
        }

        // Validation passed
        return UserValidator.returnPassedData({
            userId: userId,
        });
    }
}

module.exports = UserValidator;