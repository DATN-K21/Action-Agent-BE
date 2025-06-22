const https = require('https');
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

function fetchFromUrl(url) {
    return new Promise((resolve, reject) => {
        https.get(url, (response) => {
            let data = '';

            response.on('data', (chunk) => {
                data += chunk;
            });

            response.on('end', () => {
                try {
                    resolve(data);
                } catch (error) {
                    reject(error);
                }
            });
        }).on('error', (error) => {
            reject(error);
        });
    });
}

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
};
