const { ConflictResponse, NotFoundResponse } = require("../../response/error");
const { generateRandomString } = require("../../utils/crypto.util");
const MongooseUtil = require("../../utils/mongoose.util");

class RoleService {
    constructor() {
        this.roleModel = require('./role.model');
    }

    populateGrantListPipeLine() {
        const pipeline = [];
        pipeline.push({
            $unwind: "$grants"
        });
        pipeline.push({
            $lookup: {
                from: "Resources",
                localField: "grants.resource",
                foreignField: "_id",
                as: "resource"
            }
        });
        pipeline.push({
            $unwind: "$resource"
        });
        pipeline.push({
            $project: {
                role: "$name",
                description: 1,
                resource: "$resource.name",
                action: "$grants.actions",
                attributes: '$grants.attributes',
            }
        });
        pipeline.push({
            $unwind: "$action"
        });
        pipeline.push({
            $project: {
                _id: 0,
                role: 1,
                resource: 1,
                action: "$action",
                attributes: 1,
            }
        });
        return pipeline;
    }

    async createNewRole(userId, name, description, grants) {
        const existingRole = await this.roleModel.findOne({ name });
        if (existingRole) {
            throw new ConflictResponse('Role already exists', 1030105);
        }

        const slug = generateRandomString(10);
        return this.roleModel.create({
            slug, name, description, grants, owners: [MongooseUtil.convertToMongooseObjectIdType(userId)]
        });
    }

    async getRoleList({ limit = undefined, page = undefined, search = '', sort = undefined, sortOrder = 1 }) {
        const pipeline = [];
        // Search query filter
        if (search && search.trim() !== '') {
            pipeline.push({
                $match: {
                    $or: [
                        { slug: { $regex: search, $options: 'i' } },
                        { name: { $regex: search, $options: 'i' } },
                        { description: { $regex: search, $options: 'i' } },
                    ]
                }
            });
        }

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

        const roleData = await this.roleModel.aggregate(pipeline);
        return {
            data: roleData[0]?.results,
            total: roleData[0]?.totalCount[0] ? roleData[0]?.totalCount[0]?.count : 0,
        };
    }

    async getRoleById(id) {
        const foundRole = await this.roleModel.findById(MongooseUtil.convertToMongooseObjectIdType(id));
        if (!foundRole) {
            throw new NotFoundResponse('Role not found', 1030303);
        }
        return foundRole;
    }

    async getRoleByName(roleName) {
        const foundRole = await this.roleModel.findOne({ name: roleName }).lean();
        if (!foundRole) {
            throw new NotFoundResponse('Role not found', 1030303);
        }
        return foundRole;
    }

    async updateRole(roleId, { slug, name, description, grants }) {
        const foundRole = await this.roleModel.findById(MongooseUtil.convertToMongooseObjectIdType(roleId));
        if (!foundRole) {
            throw new NotFoundResponse('Role not found', 1030404);
        }

        if (slug) {
            foundRole.slug = slug;
        }
        if (name) {
            foundRole.name = name;
        }
        if (description) {
            foundRole.description = description;
        }

        if (grants) {
            foundRole.grants = grants.map(x => x);
        }

        const result = await foundRole.save();
        return result._doc;
    }

    async deleteRole(roleId) {
        const foundRole = await this.roleModel.findById(MongooseUtil.convertToMongooseObjectIdType(roleId));
        if (!foundRole) {
            throw new NotFoundResponse('Role not found', 1030503);
        }

        return await this.roleModel.deleteOne({ _id: MongooseUtil.convertToMongooseObjectIdType(roleId) });
    }

    async getPermissionGrantList({ limit = undefined, page = undefined, search = '', sort = undefined, sortOrder = 1 }) {
        const pipeline = this.populateGrantListPipeLine();

        // Search query filter
        if (search && search.trim() !== '') {
            pipeline.push({
                $match: {
                    $or: [
                        { role: { $regex: search, $options: 'i' } },
                        { resource: { $regex: search, $options: 'i' } },
                        { action: { $regex: search, $options: 'i' } }
                    ]
                }
            });
        }

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

        const roleData = await this.roleModel.aggregate(pipeline);
        return {
            data: roleData[0]?.results,
            total: roleData[0]?.totalCount[0] ? roleData[0]?.totalCount[0]?.count : 0,
        };
    }

    async addNewGrantsToRole(roleId, newGrant) {
        const foundRole = await this.roleModel.findById(MongooseUtil.convertToMongooseObjectIdType(roleId));
        if (!foundRole) {
            throw new NotFoundResponse('Role not found', 1030705);
        }

        foundRole.grants = [...foundRole.grants, newGrant];
        const result = await foundRole.save();
        return result._doc;
    }

    async getGrantsByRole(roleId) {
        const foundRole = await this.roleModel.findById(MongooseUtil.convertToMongooseObjectIdType(roleId))
            .populate('grants.resource').lean();
        if (!foundRole) {
            throw new NotFoundResponse('Role not found', 1030805);
        }

        return foundRole.grants;
    }
}

module.exports = RoleService;