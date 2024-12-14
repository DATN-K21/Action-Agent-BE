require('dotenv').config();

const { OAuth2Client } = require('google-auth-library');
const client = new OAuth2Client(process.env.AUTH_GOOGLE_CLIENT_ID, process.env.AUTH_GOOGLE_SECRET);

class GoogleHelper {
    static async verifyIdToken(idToken) {
        try {
            const ticket = await client.verifyIdToken({
                idToken,
                audience: process.env.AUTH_GOOGLE_CLIENT_ID,
            });

            const payload = ticket.getPayload();
            return {
                googleId: payload.sub, // ID người dùng trên Google
                email: payload.email,
                name: payload.name,
                picture: payload.picture,
            };
        }
        catch (error) {
            return null;
        }

    }
}

module.exports = GoogleHelper;