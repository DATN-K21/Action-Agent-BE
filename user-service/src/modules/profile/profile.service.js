const { NotFoundResponse, ConflictResponse } = require("../../response/error");
const MongooseUtil = require("../../utils/mongoose.util");
const UserFilter = require("../user/user.filter");
const UserService = require("../user/user.service");
const ProfileFilter = require("./profile.filter");


class ProfileService {
    constructor() {
        this.profileModel = require("./profile.model");
        this.userModel = require("../user/user.model");
        this.userService = new UserService();
    }

    populateProfilePipeLineWithUser(oldPipeline = []) {
        // const pipeline = Array.isArray(oldPipeline) ? [...oldPipeline] : [];
        const pipeline = oldPipeline.map(item => item);
        // Lookup user
        pipeline.push({
            $lookup: {
                from: 'Users',
                localField: 'user_id',
                foreignField: '_id',
                as: 'user'
            }
        });
        pipeline.push({
            $unwind: '$user',
        });
        // Lookup role
        pipeline.push({
            $lookup: {
                from: 'Roles',
                localField: 'user.role',
                foreignField: '_id',
                as: 'role'
            }
        });
        pipeline.push({
            $unwind: '$role',
        });
        pipeline.push({
            $addFields: {
                username: '$user.username',
                email: '$user.email',
                fullname: '$user.fullname',
                avatar: '$user.avatar',
                verified: '$user.email_verified',
                role: '$role.name',
            }
        });
        pipeline.push({
            $project: {
                user: 0, // Exclude the user field
                __v: 0,
            }
        });

        return pipeline;
    }

    async createNewProfile(profileData) {
        // API Code starts from 1050128
        const userId = profileData?.user_id;
        const foundUser = await this.userModel.findById(MongooseUtil.convertToMongooseObjectIdType(userId));
        if (!foundUser) {
            throw new NotFoundResponse("User not found", 1050128);
        }

        const existingProfile = await this.profileModel.findOne({ user_id: userId });
        if (existingProfile) {
            throw new ConflictResponse("Profile already exists", 1050129);
        }

        if (foundUser?.email !== profileData?.emails[0]) {
            const existingEmail = await this.userModel.findOne({ email: profileData?.emails[0] });
            if (existingEmail) {
                throw new ConflictResponse("Email already in use", 1050130);
            }
        }

        const newProfile = await this.profileModel.create({
            user_id: userId,
            owners: [foundUser._id],
            ...profileData,
        });

        const returnedProfile = {
            ...ProfileFilter.makeBasicFilter(newProfile),
            user: UserFilter.makeBasicFilter(foundUser),
            user_id: undefined,
        }
        return returnedProfile;
    }

    async getProfileList({ limit, page, search, sort, sortOrder = 1 }) {
        let pipeline = [];
        // Search query filter
        if (search && search.trim() !== '') {
            pipeline.push({
                $match: {
                    $or: [
                        { slug: { $regex: search, $options: 'i' } },
                        { username: { $regex: search, $options: 'i' } },
                        { email: { $regex: search, $options: 'i' } },
                        { fullname: { $regex: search, $options: 'i' } },
                    ]
                }
            });
        }


        pipeline = this.populateProfilePipeLineWithUser(pipeline);

        // Add $facet stage to handle both total count and paginated results
        pipeline.push({
            $facet: {
                totalCount: [{ $count: 'count' }],

                results: [
                    // Sort
                    ...(sort ? [{ $sort: { [sort]: +sortOrder } }] : []),
                    // Pagination
                    ...(limit ? [{ $limit: limit }] : []),
                    ...(page ? [{ $skip: (page - 1) * limit }] : [])
                ]
            }
        });


        const profileData = await this.profileModel.aggregate(pipeline);
        return {
            data: profileData[0]?.results,
            total: profileData[0]?.totalCount[0] ? profileData[0]?.totalCount[0]?.count : 0,
        };
    }

    async getProfileById(profileId) {
        const foundProfile = await this.profileModel.findById(MongooseUtil.convertToMongooseObjectIdType(profileId)).lean();
        if (!foundProfile) {
            throw new NotFoundResponse('Profile not found', 1050303);
        }

        const foundUser = await this.userService.getUserById(foundProfile.user_id);
        if (!foundUser) {
            throw new ConflictResponse('Something went wrong', 1050304);
        }

        const returnedProfile = {
            ...ProfileFilter.makeDetailFilter(foundProfile),
            user: UserFilter.makeDetailFilter(foundUser),
            user_id: undefined,
        }
        return returnedProfile;
    }

    async updateProfile(profileId, profileData) {
        const foundProfile = await this.profileModel.findById(MongooseUtil.convertToMongooseObjectIdType(profileId));
        if (!foundProfile) {
            throw new NotFoundResponse('Profile not found', 1050426);
        }

        const foundUser = await this.userService.getUserById(foundProfile.user_id);
        if (!foundUser) {
            throw new ConflictResponse('Something went wrong', 1050427);
        }

        if (profileData?.nickname && !foundProfile.nicknames.includes(profileData.nickname)) {
            foundProfile.nicknames.push(profileData.nickname);
        }
        if (profileData?.bio && foundProfile.bio !== profileData.bio) {
            foundProfile.bio = profileData.bio;
        }
        if (profileData?.gender && foundProfile.gender !== profileData.gender) {
            foundProfile.gender = profileData.gender;
        }
        if (profileData?.date_of_birth && foundProfile.date_of_birth !== profileData.date_of_birth) {
            foundProfile.date_of_birth = profileData.date_of_birth;
        }
        if (profileData?.avatar && !foundProfile.avatars.includes(profileData.avatar)) {
            foundProfile.avatars.push(profileData.avatar);
        }
        if (profileData?.cover_photo && !foundProfile.cover_photos.includes(profileData.cover_photo)) {
            foundProfile.cover_photos.push(profileData.cover_photo);
        }
        if (profileData?.email) {
            if (foundUser?.email !== profileData?.email) {
                const existingEmail = await this.userModel.findOne({ email: profileData?.email });
                if (existingEmail) {
                    throw new ConflictResponse("Email already in use", 1050405);
                }
            } else {
                foundProfile.emails.push(profileData.email);
            }
        }
        if (profileData?.phone && !foundProfile.phones.includes(profileData.phone)) {
            foundProfile.phones.push(profileData.phone);
        }
        if (profileData?.address && !foundProfile.addresses.includes(profileData.address)) {
            foundProfile.addresses.push(profileData.address);
        }
        if (profileData?.social && !foundProfile.socials.includes(profileData.social)) {
            foundProfile.socials.push(profileData.social);
        }
        if (profileData?.workplace && !foundProfile.workplaces.includes(profileData.workplace)) {
            foundProfile.workplaces.push(profileData.workplace);
        }
        if (profileData?.education && !foundProfile.educations.includes(profileData.education)) {
            foundProfile.educations.push(profileData.education);
        }

        const updatedProfile = await foundProfile.save();
        const returnedProfile = {
            ...ProfileFilter.makeDetailFilter(updatedProfile._doc),
            user: UserFilter.makeDetailFilter(foundUser),
            user_id: undefined,
        }
        return returnedProfile;
    }

    async deleteProfile(profileId) {
        const foundProfile = await this.profileModel.findById(MongooseUtil.convertToMongooseObjectIdType(profileId));
        if (!foundProfile) {
            throw new NotFoundResponse('Profile not found', 1050503);
        }

        const foundUser = await this.userService.getUserById(foundProfile.user_id);
        if (!foundUser) {
            throw new ConflictResponse('Something went wrong', 1050504);
        }

        await this.profileModel.deleteOne({ _id: foundProfile._id });
    }
}

module.exports = ProfileService;