const RoleService = require("../modules/role/role.service");
const { UnauthorizedResponse, BadRequestResponse } = require("../response/error");
const AccessControl = require('accesscontrol');
const MongooseUtil = require("../utils/mongoose.util");
const PermissionConfig = require('../configs/permission.config');

class PermissionMiddleware {
    constructor() {
        this.ac = new AccessControl();
        this.roleService = new RoleService();
    }

    formatAction(action, destination = "DB") {
        const preAction = action.slice(0, -3);
        const postAction = action.slice(-3);
        switch (destination) {
            case 'DB':
                return `${preAction}:${postAction.toLowerCase()}`;
            case 'AC':
                return `${preAction}${postAction.charAt(0).toUpperCase()}${postAction.slice(1)}`;

            default: return action;
        }
    }

    findPermissionInRole(grant, action) {
        const formattedAction = this.formatAction(action);
        let foundPermission = grant.actions.find(grantAction => grantAction === formattedAction);

        return foundPermission;
    }

    /**
     * This middleware MUST be called after checkAccess middleware
     */
    checkPermission(resource, getResourceOwnerIds) {
        return async (req, res, next) => {
            const reqMethod = req.method.toLowerCase();
            const action = PermissionConfig.getPermissionAction(reqMethod, resource);
            try {
                const foundGrantList = await this.roleService.getPermissionGrantList({});
                if (!foundGrantList || !foundGrantList.data || !foundGrantList.data.length) {
                    throw new UnauthorizedResponse('Something went wrong', 1000201);
                }

                this.ac.setGrants(foundGrantList.data);
                // Retrieve req.user from checkAccess middleware
                const user = req.user;
                const foundRole = await this.roleService.getRoleByName(user?.role);
                if (!foundRole || !foundRole.grants || !foundRole.name) {
                    throw new UnauthorizedResponse('Access denied', 1000202);
                }

                const permission = this.ac.can(foundRole.name)[action](resource);
                if (!permission || !permission?.granted || permission?.granted === false) {
                    throw new UnauthorizedResponse('Access denied', 1000203);
                }

                /*
                    If both the action and found permission is "Own", 
                    then we need to check if the resource owner is the same as the requesting user
                */
                const foundGrants = await this.roleService.getGrantsByRole(foundRole._id);
                const foundGrant = foundGrants.find(grant => grant.resource.name === resource);
                if (!foundGrant || !foundGrant.resource || !foundGrant.actions || !foundGrant.attributes) {
                    throw new UnauthorizedResponse('Access denied', 1000204);
                } else if (!foundGrant.resource.name || foundGrant.resource.name !== resource) {
                    throw new UnauthorizedResponse('Access denied', 1000205);
                }
                const foundPermission = this.findPermissionInRole(foundGrant, action);

                const isOwnAction = action.endsWith('Own');
                if (isOwnAction && foundPermission) {
                    const resourceOwners = await getResourceOwnerIds(req);
                    if (!resourceOwners || !Array.isArray(resourceOwners) || !resourceOwners.length || resourceOwners.length <= 0) {
                        throw new UnauthorizedResponse('Access denied', 1000206);
                    } else if (!resourceOwners.includes(user.id)) {
                        throw new UnauthorizedResponse('Access denied', 1000207);
                    }
                }

                return next();
            } catch (error) {
                if (MongooseUtil.isMongooseError(error)) {
                    return next(new BadRequestResponse("Something went wrong", 1000208));
                }
                return next(error);
            }
        };
    }
}

module.exports = new PermissionMiddleware();