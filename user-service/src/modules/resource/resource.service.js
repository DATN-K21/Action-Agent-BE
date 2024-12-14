const { ConflictResponse, NotFoundResponse } = require("../../response/error");
const { generateRandomString } = require("../../utils/crypto.util");
const MongooseUtil = require("../../utils/mongoose.util");

class ResourceService {
    constructor() {
        this.resourceModel = require('./resource.model');
    }

    async createNewResource(userId, name, description) {
        const existingResource = await this.resourceModel.findOne({ name });
        if (existingResource) {
            throw new ConflictResponse('Resource already exists', 1020103);
        }

        const slug = generateRandomString(10);
        return this.resourceModel.create({
            slug, name, description, owners: [MongooseUtil.convertToMongooseObjectIdType(userId)]
        });
    }

    async getResourceList({ limit, page, search, sort, sortOrder = 1 }) {
        try {
            const pipeline = [];
            // Search query filter
            if (search && search.trim() !== '') {
                pipeline.push({
                    $match: {
                        $or: [
                            { slug: { $regex: search, $options: 'i' } },
                            { name: { $regex: search, $options: 'i' } },
                            { description: { $regex: search, $options: 'i' } }
                        ]
                    }
                });
            }
            // Project only necessary fields
            pipeline.push({
                $project: {
                    _id: 0,
                    id: '$_id',
                    slug: 1,
                    name: 1,
                    description: 1,
                }
            });
            // Sort
            if (sort) {
                pipeline.push({
                    $sort: {
                        [sort]: +sortOrder
                    }
                });
            }
            // Pagination
            if (limit) {
                pipeline.push({ $limit: limit });
            }
            if (page) {
                pipeline.push({ $skip: (page - 1) * limit });
            }

            const resources = this.resourceModel.aggregate(pipeline);
            return resources;
        } catch (error) {
            console.log("Error in get all resources: ", error);
            return [];
        }
    }

    async getResourceById(id) {
        const foundResource = await this.resourceModel.findById(MongooseUtil.convertToMongooseObjectIdType(id));
        if (!foundResource) {
            throw new NotFoundResponse('Resource not found', 1020303);
        }

        return foundResource;
    }

    async updateResource(resourceId, { slug, name, description }) {
        const foundResource = await this.resourceModel.findById(MongooseUtil.convertToMongooseObjectIdType(resourceId));
        if (!foundResource) {
            throw new NotFoundResponse('Resource not found', 1020404);
        }

        if (slug) {
            foundResource.slug = slug;
        }
        if (name) {
            foundResource.name = name;
        }
        if (description) {
            foundResource.description = description;
        }

        return await foundResource.save();
    }

    async deleteResource(resourceId) {
        const foundResource = await this.resourceModel.findById(MongooseUtil.convertToMongooseObjectIdType(resourceId));
        if (!foundResource) {
            throw new NotFoundResponse('Resource not found', 1020503);
        }

        return await this.resourceModel.deleteOne({ _id: MongooseUtil.convertToMongooseObjectIdType(resourceId) });
    }
}

module.exports = ResourceService;