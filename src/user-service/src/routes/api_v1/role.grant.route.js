const permissionMiddleware = require('../../middlewares/permission.middleware');
const roleController = require('../../modules/role/role.controller');
const handleAsync = require('../../utils/asyncHandler.util');

const router = require('express').Router();

// This router has already been checked for the access through role.route.js

// Other SUP-ROUTES imported here
// For example: router.use('/avatar', require('./avatar.route'));





// IMPORTANT: Common routes middleware, sup-routes imported ABOVE this line
router.use((req, res, next) => {
    const id = req.path.split("/")[1];
    req.params.id = id;

    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds))(req, res, next);
})

router.get('', handleAsync(roleController.getPermissionGrantList));
router.get('/:id', handleAsync(roleController.getGrantsByRole));

router.patch("/:id", handleAsync(roleController.addNewGrantsToRole));

module.exports = router;