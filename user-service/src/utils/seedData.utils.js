const https = require('https');

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

module.exports = {
    parseObjectIds,
    fetchFromUrl
};