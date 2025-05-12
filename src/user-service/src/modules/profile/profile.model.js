const mongoose = require('mongoose'); // Erase if already required

// Declare the Schema of the Mongo model
var profileSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, required: true, ref: 'User' },
    // GENERAL
    nicknames: [{ type: String, default: '' }],
    bio: { type: String, default: '' },
    gender: { type: String, default: 'unknown', enum: ['unknown', 'male', 'female', 'other'] },
    date_of_birth: { type: Date, default: Date.now() },
    // IMAGES
    avatars: [{
        url: { type: String, required: true },
        uploadedAt: { type: Date, default: Date.now() },
    }],
    cover_photos: [{
        url: { type: String, required: true },
        uploadedAt: { type: Date, default: Date.now() },
    }],
    service_photos: [{
        url: { type: String, required: true },
        serviceUrl: { type: String, required: true },
        serviceId: { type: mongoose.Types.ObjectId, required: true, ref: 'Service' },
        uploadedAt: { type: Date, default: Date.now() },
    }],
    // CONTACT
    emails: [{ type: String, default: '' }],
    phones: [{ type: String, default: '' }],
    addresses: [{
        street: { type: String, default: '' },
        city: { type: String, default: '' },
        state: { type: String, default: '' },
        country: { type: String, default: '' },
        postal_code: { type: String, default: '' },
    }],
    socials: [{
        name: { type: String, required: true, enum: ['facebook', 'twitter', 'instagram', 'linkedin', 'github', 'website'] },
        url: { type: String, required: true },
    }],
    // WORK
    workplaces: [{ type: String, default: '' }],
    educations: [{ type: String, default: '' }],
    owners: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
}, {
    timestamps: true,
    collection: 'Profiles'
});

//Export the model
module.exports = mongoose.model('Profile', profileSchema);