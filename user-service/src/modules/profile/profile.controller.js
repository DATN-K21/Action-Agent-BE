const { BadRequestResponse } = require("../../response/error");
const { CreatedSuccessResponse, OKSuccessResponse } = require("../../response/success");
const MongooseUtil = require("../../utils/mongoose.util");
const ProfileService = require("./profile.service");
const ProfileValidator = require("./profile.validator");

class ProfileController {
    constructor() {
        this.profileService = new ProfileService();
    }

    getProfileOwnerIds = async (req) => {
        const profileId = req.params?.id;
        if (!profileId) {
            // The request is not for a specific profile, so it does not have a specific owner
            return [];
        }
        const foundProfile = await this.profileService.getProfileById(profileId);
        return foundProfile?.owners?.map(x => x.toString()) ?? [];
    };


    createNewProfile = async (req, res, next) => {
        const validationResult = ProfileValidator.validateCreateNewProfile(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { profileData } = validationResult?.data;
        try {
            const result = await this.profileService.createNewProfile(profileData);
            return new CreatedSuccessResponse({
                message: 'Create new profile success',
                data: result,
                code: 1050100
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1050131);
            }
            throw error;
        }
    }

    getProfileList = async (req, res, next) => {
        const validationResult = ProfileValidator.validateGetProfileList(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { filter } = validationResult?.data;
        try {
            const result = await this.profileService.getProfileList(filter);
            return new OKSuccessResponse({
                message: 'Get profile list success',
                data: result.data,
                code: 1050200,
                metadata: {
                    total: result?.total ?? undefined,
                    page: filter?.page ?? undefined,
                    perpage: filter?.limit ?? undefined,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1050206);
            }
            throw error;
        }
    };

    getProfileById = async (req, res, next) => {
        const validationResult = ProfileValidator.validateGetProfileById(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { profileId } = validationResult?.data;
        try {
            const result = await this.profileService.getProfileById(profileId);
            return new OKSuccessResponse({
                message: 'Get profile by id success',
                data: result,
                code: 1050300
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1050399);
            }
            throw error;
        }
    }

    updateProfile = async (req, res, next) => {
        const validationResult = ProfileValidator.validateUpdateProfile(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { profileId, profileData } = validationResult?.data;
        try {
            const result = await this.profileService.updateProfile(profileId, profileData);
            return new OKSuccessResponse({
                message: 'Update profile success',
                data: result,
                code: 1050400
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1050427);
            }
            throw error;
        }
    }

    deleteProfile = async (req, res, next) => {
        const validationResult = ProfileValidator.validateDeleteProfile(req);
        if (validationResult?.error === true) {
            throw new BadRequestResponse(validationResult?.message ?? "", validationResult?.code ?? -1);
        }

        const { profileId } = validationResult?.data;
        try {
            const result = await this.profileService.deleteProfile(profileId);
            return new OKSuccessResponse({
                message: 'Delete profile success',
                data: {
                    deleted: profileId,
                },
                metadata: {
                    code: 1050500,
                    ...result,
                }
            }).send(res);
        } catch (error) {
            if (MongooseUtil.isMongooseError(error)) {
                throw new BadRequestResponse("Something went wrong", 1050505);
            }
            throw error;
        }
    }
}

module.exports = new ProfileController();