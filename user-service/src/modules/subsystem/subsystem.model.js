const mongoose = require('mongoose'); // Erase if already required

// Declare the Schema of the Mongo model
var subSystemSchema = new mongoose.Schema({
    name: { type: String, required: true },
    description: { type: String, required: true },
    apiKeys: { type: String, required: true },
    status: { type: String, default: 'inactive', enum: ['active', 'inactive', 'blocked', 'maintaining'] },
    owners: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    logo_url: { type: String, default: '' },
}, {
    timestamps: true,
    collection: 'SubSystems'
});

//Export the model
module.exports = mongoose.model('SubSystem', subSystemSchema);