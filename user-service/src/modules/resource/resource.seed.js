const Resource = require('./resource.model');
const { parseObjectIds, fetchFromUrl } = require('../../utils/seedData.utils');

module.exports = async function seedResources(mongoose) {
    const resourcesData = await fetchFromUrl('https://gist.githubusercontent.com/thienan2003bt/ca53b2a91e860b12f38b6d3156b0ccb7/raw/15c52be844e3cd0c370e71864465a8fd0bde2b0f/datn-user-database.Resources.json');
    const parsedResources = JSON.parse(resourcesData);

    for (const rawResource of parsedResources) {
        const resource = await parseObjectIds(rawResource, mongoose);

        await Resource.findOneAndUpdate(
            { _id: resource._id },
            resource,
            { upsert: true, new: true, setDefaultsOnInsert: true }
        );
    }

    return parsedResources.length;
};
