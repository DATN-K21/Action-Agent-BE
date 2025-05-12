class SubSystemUtil {
    static SUB_SYSTEMS = [{
        id: '67500f736f63d157712ed27f',
        slug: 'user-service',
        name: 'User Service',
        apiKey: '459973a262b338a413052d356087b4',
    }, {
        id: '6750069ff42ae9e9bb5b2f4e',
        slug: 'log-service',
        name: 'Log Service',
        apiKey: '4d7fed4ed626149de3180ecf3240f4',
    }];


    static getSubSystemByApiKey(apiKey) {
        return this.SUB_SYSTEMS.find(subSystem => subSystem.apiKey === apiKey);
    }
}

module.exports = SubSystemUtil;