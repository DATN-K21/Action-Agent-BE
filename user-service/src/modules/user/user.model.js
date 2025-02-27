const mongoose = require('mongoose'); // Erase if already required

// Declare the Schema of the Mongo model
const userSchema = new mongoose.Schema({
    slug: { type: String, default: '' },
    email: { type: String, default: '' },
    password: { type: String, default: '' },
    username: { type: String, default: '' },
    firstname: { type: String, default: '' },
    lastname: { type: String, default: '' },
    fullname: { type: String, default: '' },
    avatar: { type: String, default: '' },
    role: { type: mongoose.Schema.Types.ObjectId, ref: 'Role' },
    email_verified: { type: Boolean, default: false },
    type_login: { type: String, default: 'local', enum: ['local', 'google', 'facebook'] },
    google_id: { type: String, default: '' },
    facebook_id: { type: String, default: '' },
    owners: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
}, {
    timestamps: true,
    collection: 'Users'
});

//Export the model
module.exports = mongoose.model('User', userSchema);