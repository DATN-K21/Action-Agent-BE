require("dotenv").config();
const passport = require("passport");

const FacebookStrategy = require("passport-facebook").Strategy;

class FacebookHelper {
    static configureFacebookStrategy() {
        passport.use(
            new FacebookStrategy(
                {
                    clientID: process.env.FACEBOOK_APP_CLIENT_ID,
                    clientSecret: process.env.FACEBOOK_APP_CLIENT_SECRET,
                    callbackURL: process.env.FACEBOOK_APP_REDIRECT_URL,
                    profileFields: ["id", "displayName", "photos", "email"],
                    enableProof: true
                },
                async function (accessToken, refreshToken, profile, cb) {
                    return cb(null, profile);
                }
            )
        );
    }
}

module.exports = FacebookHelper;