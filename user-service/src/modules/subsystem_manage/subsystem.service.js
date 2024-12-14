
const { ConflictResponse } = require('../../response/error');
const { generateRandomString } = require('../../utils/crypto.util');
const subSystemModel = require('./subsystem.model');

class SubSystemService {
    constructor() {
        this.subSystemModel = subSystemModel;
    }

    async getSubSystemList() {
        return await this.subSystemModel.find();
    }

    async createNewSubSystem({ name, description, owner, logo_url }) {
        const foundSubSystem = await this.subSystemModel.findOne({ name: name });
        if (foundSubSystem) {
            throw new ConflictResponse('SubSystem already exists', 1060105);
        }

        const apiKeys = generateRandomString(30);

        return await this.subSystemModel.create({
            name,
            description,
            apiKeys,
            owners: [owner],
            logo_url
        });
    }
    async getSubSystemById(subSystemId) {
        const foundSubSystem = await this.subSystemModel.findById(subSystemId);
        if (!foundSubSystem) {
            throw new ConflictResponse('SubSystem not found', 1060303);
        }
        return foundSubSystem;
    }

    async updateSubSystem(subSystemId, { name, description, logo_url, status }) {
        const foundSubSystem = await this.subSystemModel.findById(subSystemId);
        if (!foundSubSystem) {
            throw new ConflictResponse('SubSystem not found', 1060406);
        }

        if (name) {
            foundSubSystem.name = name;
        }
        if (description) {
            foundSubSystem.description = description;
        }
        if (logo_url) {
            foundSubSystem.logo_url = logo_url;
        }
        if (status) {
            foundSubSystem.status = status;
        }

        const updatedSubSystem = await foundSubSystem.save();
        return updatedSubSystem._doc;
    }
    async deleteSubSystem(subSystemId) {
        const foundSubSystem = await this.subSystemModel.findById(subSystemId);
        if (!foundSubSystem) {
            throw new ConflictResponse('SubSystem not found', 1060503);
        }
        return await this.subSystemModel.deleteOne({ _id: subSystemId });
    }
}

module.exports = SubSystemService;