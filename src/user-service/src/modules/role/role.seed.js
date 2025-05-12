const fs = require('fs');
const path = require('path');
const Role = require('./role.model');

async function parseObjectIds(obj, mongoose) {
    if (Array.isArray(obj)) {
        return Promise.all(obj.map(item => parseObjectIds(item, mongoose)));
    } else if (obj && typeof obj === 'object') {
        // Case: { "$oid": "..." } → convert to ObjectId
        if (Object.keys(obj).length === 1 && obj.$oid) {
            return new mongoose.Types.ObjectId(obj.$oid);
        }

        const result = {};
        for (const key in obj) {
            result[key] = await parseObjectIds(obj[key], mongoose);
        }
        return result;
    } else {
        return obj;
    }
}

module.exports = async function seedRoles(mongoose) {
    const rolesData = fs.readFileSync(path.join(__dirname, 'roles.json'), 'utf-8');
    const parsedRoles = JSON.parse(rolesData);

    for (const rawRole of parsedRoles) {
        const role = await parseObjectIds(rawRole, mongoose);

        await Role.findOneAndUpdate(
            { _id: role._id },
            role,
            { upsert: true, new: true, setDefaultsOnInsert: true }
        );
    }
};
