const mongoose = require('mongoose');

// Declare the Schema of the Mongo model
const roleSchema = new mongoose.Schema({
    slug: { type: String, required: true },
    name: { type: String, required: true },
    description: { type: String, default: '' },
    status: { type: String, default: 'active', enum: ['active', 'blocked', 'pending'] },
    grants: [
        {
            resource: { type: mongoose.Schema.Types.ObjectId, ref: 'Resource', required: true },
            actions: [{ type: String, required: true }],
            attributes: { type: String, default: '*' },
        },
    ],
    owners: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
}, {
    timestamps: true,
    collection: 'Roles',
});

//Export the model
module.exports = mongoose.model('Role', roleSchema);