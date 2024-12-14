
class PermissionConfig {
    static USER_PERMISSION_MIDDLEWARE = {
        get: 'readAny',
        post: 'createOwn',
        patch: 'updateOwn',
        delete: 'deleteOwn',
    }

    static ACCESS_PERMISSION_MIDDLEWARE = {
        get: 'readOwn',
        post: 'createOwn',
        patch: 'updateOwn',
        delete: 'deleteAny',
    }

    static RESOURCE_PERMISSION_MIDDLEWARE = {
        get: 'readAny',
        post: 'createAny',
        patch: 'updateAny',
        delete: 'deleteAny',
    }

    static ROLE_PERMISSION_MIDDLEWARE = {
        get: 'readAny',
        post: 'createAny',
        patch: 'updateOwn',
        delete: 'deleteOwn',
    }

    static PROFILE_PERMISSION_MIDDLEWARE = {
        get: 'readOwn',
        post: 'createOwn',
        patch: 'updateOwn',
        delete: 'deleteOwn',
    }

    static SUBSYSTEM_PERMISSION_MIDDLEWARE = {
        get: 'readAny',
        post: 'createAny',
        patch: 'updateOwn',
        delete: 'deleteOwn',
    }

    static getPermissionAction(method, resource) {
        return PermissionConfig[`${resource.toUpperCase()}_PERMISSION_MIDDLEWARE`][method];
    }
}

module.exports = PermissionConfig;