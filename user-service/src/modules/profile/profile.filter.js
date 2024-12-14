
class ProfileFilter {
    static makeBasicFilter(profile) {
        return {
            id: profile?._id,
            user_id: profile?.user_id,
            nicknames: profile?.nicknames,
            bio: profile?.bio,
            emails: profile?.emails,
        }
    }

    static makeDetailFilter(profile) {
        return {
            ...profile,
            __v: undefined,
        }
    }

}

module.exports = ProfileFilter;