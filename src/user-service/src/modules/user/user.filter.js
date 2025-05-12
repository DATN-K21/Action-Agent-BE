
class UserFilter {
    static makeBasicFilter(user) {
        return {
            id: user?._id,
            email: user?.email,
            username: user?.username,
            firstname: user?.firstname,
            lastname: user?.lastname,
            fullname: user?.fullname,
        };
    }

    static makeDetailFilter(user) {
        return {
            ...user,
            password: undefined,
            __v: undefined,
        };
    }

    static filterByScope(user, scope) {
        switch (scope) {
            case 'basic':
                return UserFilter.makeBasicFilter(user);
            case 'detail':
                return UserFilter.makeDetailFilter(user);
            default:
                return UserFilter.makeBasicFilter(user);
        }
    }
}

module.exports = UserFilter;
