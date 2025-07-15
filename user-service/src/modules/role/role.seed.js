
const Role = require('./role.model');
const { parseObjectIds, fetchFromUrl } = require('../../utils/seedData.utils');

module.exports = async function seedRoles(mongoose) {
    const rolesData = await fetchFromUrl('https://gist.githubusercontent.com/git03-Nguyen/1d96a3fe5e292bbe9901a38650d81163/raw/2ef6581e9dbd50060f6c932032558a1815021d0e/roles.json');
    const parsedRoles = JSON.parse(rolesData);

    for (const rawRole of parsedRoles) {
        const role = await parseObjectIds(rawRole, mongoose);

        await Role.findOneAndUpdate(
            { _id: role._id },
            role,
            { upsert: true, new: true, setDefaultsOnInsert: true }
        );
    }

    return parsedRoles.length;
};
