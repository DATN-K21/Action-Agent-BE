const mongoose = require('mongoose');

// Declare the Schema of the Mongo model
const resourceSchema = new mongoose.Schema({
    slug: { type: String, required: true },
    name: { type: String, required: true },
    description: { type: String, default: '' },
    owners: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
}, {
    timestamps: true,
    collection: 'Resources',
});

//Export the model
module.exports = mongoose.model('Resource', resourceSchema);