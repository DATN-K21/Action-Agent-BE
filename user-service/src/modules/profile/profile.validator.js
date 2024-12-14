const { get } = require("mongoose");
const ValidatorConfig = require("../../configs/validator.config");
const validator = require('validator');

class ProfileValidator extends ValidatorConfig {
    static getProfileAttributes() {
        return ['user_id', 'nickname', 'bio', 'gender', 'date_of_birth', 'avatar', 'cover_photo', 'email', 'phone', 'address', 'social', 'workplace', 'education'];
    }

    static getSortableAttributes() {
        return ['user_id', 'nickname', 'bio', 'gender', 'date_of_birth'];
    }

    static getGenderList() {
        return ['unknown', 'male', 'female', 'other'];
    }

    static getSocialNameList() {
        return ['facebook', 'twitter', 'instagram', 'linkedin', 'github', 'website'];
    }

    static getMinUserAgeValidation() {
        return 18;
    }

    static getNewAPICodeAfterValidationOptionalData(startAPICode) {
        return startAPICode + 23;
    }

    static validateOptionalAttributes(dataSource, startAPICode) {
        // Nickname validation
        if (dataSource?.nickname && !validator.isLength(dataSource?.nickname, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of nickname must between 3 and 100', startAPICode);
        }
        // Bio validation
        if (dataSource?.bio && !validator.isLength(dataSource?.bio, { min: 3, max: 500 })) {
            return ProfileValidator.returnFailedError('The length of bio must between 3 and 500', startAPICode + 1);
        }
        // Gender validation
        if (dataSource?.gender && !validator.isIn(dataSource.gender, ProfileValidator.getGenderList())) {
            return ProfileValidator.returnFailedError('Gender is invalid', startAPICode + 2);
        }
        // Date of birth validation
        if (dataSource?.date_of_birth && !validator.isDate(dataSource.date_of_birth)) {
            return ProfileValidator.returnFailedError('Date of birth is invalid', startAPICode + 3);
        } else if (dataSource?.date_of_birth && new Date(dataSource.date_of_birth) > new Date()) {
            return ProfileValidator.returnFailedError('Date of birth must be less than current date', startAPICode + 4);
        } else if (dataSource?.date_of_birth && new Date().getFullYear() - new Date(dataSource.date_of_birth).getFullYear() < ProfileValidator.getMinUserAgeValidation()) {
            return ProfileValidator.returnFailedError(`Date of birth must be at least ${ProfileValidator.getMinUserAgeValidation()} years old`, startAPICode + 5);
        }
        // Avatar validation
        if (dataSource?.avatar && !validator.isURL(dataSource.avatar)) {
            return ProfileValidator.returnFailedError('Avatar URL is invalid', startAPICode + 6);
        } else if (dataSource?.avatar && !dataSource?.avatar.includes('https://') && !dataSource?.avatar.includes('http://')) {
            return ProfileValidator.returnFailedError('Avatar URL must be a valid URL', startAPICode + 7);
        }
        // Cover photo validation
        if (dataSource?.cover_photo && !validator.isURL(dataSource.cover_photo)) {
            return ProfileValidator.returnFailedError('Cover photo URL is invalid', startAPICode + 8);
        } else if (dataSource?.cover_photo && !dataSource?.cover_photo.includes('https://') && !dataSource?.cover_photo.includes('http://')) {
            return ProfileValidator.returnFailedError('Cover photo URL must be a valid URL', startAPICode + 9);
        }
        // Email validation
        if (dataSource?.email && !validator.isEmail(dataSource.email)) {
            return ProfileValidator.returnFailedError('Email is invalid', startAPICode + 10);
        }
        // Phone validation
        if (dataSource?.phone && !validator.isMobilePhone(dataSource.phone, 'any')) {
            return ProfileValidator.returnFailedError('Phone is invalid', startAPICode + 11);
        }
        // Address validation
        if (dataSource?.address && dataSource?.address?.street && validator.isLength(dataSource?.address?.street, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of address street must between 3 and 100', startAPICode + 12);
        } else if (dataSource?.address && dataSource?.address?.city && validator.isLength(dataSource?.address?.city, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of address city must between 3 and 100', startAPICode + 13);
        } else if (dataSource?.address && dataSource?.address?.state && validator.isLength(dataSource?.address?.state, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of address state must between 3 and 100', startAPICode + 14);
        } else if (dataSource?.address && dataSource?.address?.country && validator.isLength(dataSource?.address?.country, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of address country must between 3 and 100', startAPICode + 15);
        } else if (dataSource?.address && dataSource?.address?.postal_code && validator.isPostalCode(dataSource?.address?.postal_code, 'any')) {
            return ProfileValidator.returnFailedError('Postal code is invalid', startAPICode + 16);
        }
        // Social validation
        if (dataSource?.social && validator.isEmpty(dataSource?.social.name ?? "")) {
            return ProfileValidator.returnFailedError('Social name is required', startAPICode + 17);
        } else if (dataSource?.social && validator.isEmpty(dataSource?.social?.url ?? "")) {
            return ProfileValidator.returnFailedError('Social URL is required', startAPICode + 18);
        } else if (dataSource?.social && dataSource?.social?.name && !validator.isIn(dataSource.social.name, ProfileValidator.getSocialNameList())) {
            return ProfileValidator.returnFailedError('Social name is invalid', startAPICode + 19);
        } else if (dataSource?.social && dataSource?.social?.url && !validator.isURL(dataSource.social.url)) {
            return ProfileValidator.returnFailedError('Social URL is invalid', startAPICode + 20);
        }
        // Workplace validation
        if (dataSource?.workplace && validator.isLength(dataSource?.workplace, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of workplace must between 3 and 100', startAPICode + 21);
        }
        // Education validation
        if (dataSource?.education && validator.isLength(dataSource?.education, { min: 3, max: 100 })) {
            return ProfileValidator.returnFailedError('The length of education must between 3 and 100', startAPICode + 22);
        }

        // Validation passed
        return ProfileValidator.returnPassedData({
            validatedOptionalData: {
                nickname: dataSource?.nickname ?? undefined,
                bio: dataSource?.bio ?? undefined,
                gender: dataSource?.gender ?? undefined,
                date_of_birth: dataSource?.date_of_birth ?? undefined,
                avatar: dataSource?.avatar ? {
                    url: dataSource?.avatar,
                    uploadedAt: new Date(),
                } : undefined,
                cover_photo: dataSource?.cover_photo ? {
                    url: dataSource?.cover_photo,
                    uploadedAt: new Date(),
                } : undefined,
                email: dataSource?.email ?? undefined,
                phone: dataSource?.phone ?? undefined,
                address: dataSource?.address ? {
                    street: dataSource?.address?.street ?? undefined,
                    city: dataSource?.address?.city ?? undefined,
                    state: dataSource?.address?.state ?? undefined,
                    country: dataSource?.address?.country ?? undefined,
                    postal_code: dataSource?.address?.postal_code ?? undefined,
                } : undefined,
                social: dataSource?.social ? {
                    name: dataSource?.social?.name,
                    url: dataSource?.social?.url,
                } : undefined,
                workplace: dataSource?.workplace ?? undefined,
                education: dataSource?.education ?? undefined,
            }
        });
    }

    static validateCreateNewProfile(req) {
        // User ID validation
        if (!req?.body?.user_id) {
            return ProfileValidator.returnFailedError('User ID is required', 1050101);
        } else if (!validator.isMongoId(req.body?.user_id)) {
            return ProfileValidator.returnFailedError('User ID is invalid', 1050102);
        }

        // Email validation
        if (validator.isEmpty(req.body?.email || '')) {
            return ProfileValidator.returnFailedError('Profile email is required', 1050103);
        } else if (!validator.isEmail(req.body?.email)) {
            return ProfileValidator.returnFailedError('Profile email is invalid', 1050104);
        }

        // Optional attributes validation
        // Possible API code: 1050105 - 1050127, start = 1050105
        // 1050105, 1050106, 1050107, 1050108, 1050109, 
        // 1050110, 1050111, 1050112, 1050113, 1050114, 1050115, 1050116, 1050117, 1050118, 1050119, 
        // 1050120, 1050121, 1050122, 1050123, 1050124, 1050125, 1050126, 1050127
        const validationResult = ProfileValidator.validateOptionalAttributes(req.body, 1050105);
        if (validationResult?.error === true) {
            return ProfileValidator.returnFailedError(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { validatedOptionalData } = validationResult?.data;

        return ProfileValidator.returnPassedData({
            profileData: {
                ...validatedOptionalData,
                user_id: req.body.user_id,
                emails: [req.body.email],
            },
        });
    }

    static validateGetProfileList(req) {
        let filter = req.query;
        if (filter) {
            // Limit validation
            if (filter.limit && !validator.isInt(filter.limit)) {
                return ProfileValidator.returnFailedError('Limit must be an integer', 1050201);
            }

            // Page validation
            if (filter.page && !validator.isInt(filter.page)) {
                return ProfileValidator.returnFailedError('Page must be an integer', 1050202);
            }

            // Sort validation
            if (filter.sort && !validator.isIn(filter.sort, ProfileValidator.getSortableAttributes())) {
                return ProfileValidator.returnFailedError('Sorted attribute is invalid', 1050203);
            }


            // Sort order validation
            if (!filter.sort && filter.sortOrder) {
                return ProfileValidator.returnFailedError('Sort order can only be used when sort is given', 1050204);
            } else if (filter.sortOrder && !validator.isIn(filter.sortOrder, [1, -1])) {
                return ProfileValidator.returnFailedError('Sort order must be ascending (1) or descending (-1)', 1050205);
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

        return ProfileValidator.returnPassedData({
            filter: filter
        });
    }

    static validateGetProfileById(req) {
        // Profile ID validation
        if (!req?.params?.id) {
            return ProfileValidator.returnFailedError('Profile ID is required', 1050301);
        } else if (!validator.isMongoId(req.params.id)) {
            return ProfileValidator.returnFailedError('Profile ID is invalid', 1050302);
        }

        return ProfileValidator.returnPassedData({
            profileId: req.params.id
        });
    }

    static validateUpdateProfile(req) {
        // Profile ID validation
        if (!req?.params?.id) {
            return ProfileValidator.returnFailedError('Profile ID is required', 1050401);
        } else if (!validator.isMongoId(req.params.id)) {
            return ProfileValidator.returnFailedError('Profile ID is invalid', 1050402);
        }

        // Optional attributes validation
        // Possible API code: 1050403 - 1050425, start = 1050403
        // 1050403, 1050404, 1050405, 1050406, 1050407, 
        // 1050408, 1050409, 1050410, 1050411, 1050412, 1050413, 1050414, 1050415, 1050416, 1050417, 
        // 1050418, 1050419, 1050420, 1050421, 1050422, 1050423, 1050424, 1050425
        const validationResult = ProfileValidator.validateOptionalAttributes(req.body, 1050403);
        if (validationResult?.error === true) {
            return ProfileValidator.returnFailedError(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { validatedOptionalData } = validationResult?.data;

        return ProfileValidator.returnPassedData({
            profileId: req.params.id,
            profileData: {
                ...validatedOptionalData,
            },
        });
    }

    static validateDeleteProfile(req) {
        // Profile ID validation
        if (!req?.params?.id) {
            return ProfileValidator.returnFailedError('Profile ID is required', 1050501);
        } else if (!validator.isMongoId(req.params.id)) {
            return ProfileValidator.returnFailedError('Profile ID is invalid', 1050502);
        }

        return ProfileValidator.returnPassedData({
            profileId: req.params.id
        });
    }
}

module.exports = ProfileValidator;