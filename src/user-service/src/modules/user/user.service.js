const { ConflictResponse } = require("../../response/error");
const userModel = require("./user.model");
const roleModel = require("../role/role.model");
const accessModel = require("../access/access.model");
const UserFilter = require("./user.filter");
const MongooseUtil = require("../../utils/mongoose.util");
const BcryptHelper = require("../../helpers/bcrypt.helper");
const { generateRandomString, generateRSAKeysForAccess } = require("../../utils/crypto.util");
class UserService {
    constructor() {
        this.userModel = userModel;
        this.roleModel = roleModel;
        this.accessModel = accessModel;
    }

    populateUserWithRoleNamePipeLine(oldPipeline = []) {
        const pipeline = oldPipeline.map(item => item);
        pipeline.push({
            $lookup: {
                from: 'Roles',
                localField: 'role',
                foreignField: '_id',
                as: 'role'
            }
        });
        pipeline.push({
            $project: {
                _id: 0,
                id: '$_id',
                username: 1,
                email: 1,
                fullname: 1,
                avatar: 1,
                verified: '$email_verified',
                role: { $arrayElemAt: ['$role.name', 0] },
            }
        });
        return pipeline;
    }

    async createNewUser({ username, email, password, fullname, email_verified, avatar }) {
        const existingUser = await this.userModel.findOne({ email });
        if (existingUser) {
            throw new ConflictResponse('Email already exists', 1040108);
        }

        const hashedPassword = await BcryptHelper.hash(password);
        const foundUserRole = await this.roleModel.findOne({ name: "User" }).lean();
        if (!foundUserRole) {
            throw new ConflictResponse("User role not found", 1040110);
        }

        const newUser = await this.userModel.create({
            username,
            slug: generateRandomString(10),
            email,
            password: hashedPassword,
            fullname,
            email_verified,
            avatar,
            role: foundUserRole._id,
        });

        await this.userModel.findByIdAndUpdate(newUser?._id, {
            $push: { owners: newUser?._id }
        }, { new: true });

        const { privateKey, publicKey } = generateRSAKeysForAccess();
        await this.accessModel.create({
            user_id: newUser?._id,
            public_key: publicKey.toString(),
            private_key: privateKey.toString(),
            owners: [newUser?._id]
        });

        return newUser;
    }

    async getUserList({ limit, page, search, sort, sortOrder = 1 }) {
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
        // Project only necessary fields
        pipeline = this.populateUserWithRoleNamePipeLine(pipeline);

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

        const userData = await this.userModel.aggregate(pipeline);
        return {
            data: userData[0]?.results,
            total: userData[0]?.totalCount[0] ? userData[0]?.totalCount[0]?.count : 0,
        };
    }

    async getUserById(userId) {
        const foundUser = await this.userModel.findById(MongooseUtil.convertToMongooseObjectIdType(userId)).lean();
        if (!foundUser) {
            throw new ConflictResponse('User not found', 1040303);
        }

        const foundRole = await this.roleModel.findById(foundUser.role);
        if (!foundRole) {
            throw new ConflictResponse('Something went wrong', 1040304);
        }

        return UserFilter.makeDetailFilter({
            ...foundUser,
            role: foundRole.name,
        });
    }

    async updateUser(userId, { username, password, fullname, role, email_verified, avatar, slug }) {
        const foundUser = await this.userModel.findById(MongooseUtil.convertToMongooseObjectIdType(userId));
        if (!foundUser) {
            throw new ConflictResponse('User not found', 1040408);
        }

        if (role) {
            const foundRole = await this.roleModel.findById(role).lean();
            if (!foundRole) {
                throw new ConflictResponse('Role not found', 1040409);
            }
            foundUser.role = role;
        }
        if (username) {
            foundUser.username = username;
        }
        if (password) {
            foundUser.password = await BcryptHelper.hash(password);
        }
        if (fullname) {
            foundUser.fullname = fullname;
        }
        if (role) {
            foundUser.role = role;
        }
        if (email_verified) {
            foundUser.email_verified = email_verified;
        }
        if (avatar) {
            foundUser.avatar = avatar;
        }
        if (slug) {
            foundUser.slug = slug;
        }

        const updatedUser = await foundUser.save();
        return UserFilter.makeDetailFilter(updatedUser._doc);
    }

    async deleteUser(userId) {
        const foundUser = await this.userModel.findById(MongooseUtil.convertToMongooseObjectIdType(userId));
        if (!foundUser) {
            throw new ConflictResponse('User not found', 1040503);
        }
        await this.accessModel.deleteOne({ user_id: MongooseUtil.convertToMongooseObjectIdType(userId) });
        return await this.userModel.deleteOne({ _id: foundUser._id });
    }
}

module.exports = UserService;