const mongoose = require('mongoose'); // Erase if already required

// Declare the Schema of the Mongo model
const accessSchema = new mongoose.Schema({
    user_id: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    public_key: { type: String, default: '' },
    private_key: { type: String, default: '' },
    refresh_token: { type: String, default: '' },
    refresh_token_used: [{
        token: { type: String, default: '' },
        createdAt: { type: Date, default: Date.now() },
        expiredAt: { type: Date, default: Date.now() },
    }],
    reset_password_token: { type: String, default: '' },
    otp: {
        code: { type: String, default: '' },
        expiredAt: { type: Date, default: Date.now() },
    },
    otp_count: { type: Number, default: 0 },
    last_otp_sent: { type: Date, default: null },
    otp_reset_password: {
        code: { type: String, default: '' },
        expiredAt: { type: Date, default: Date.now() },
    },
    otp_reset_password_count: { type: Number, default: 0 },
    last_otp_reset_password_sent: { type: Date, default: null },
    owners: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
}, {
    timestamps: true,
    collection: 'Access'
});

//Export the model
module.exports = mongoose.model('Access', accessSchema);