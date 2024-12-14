const permissionMiddleware = require('../../middlewares/permission.middleware');
const roleController = require('../../modules/role/role.controller');
const handleAsync = require('../../utils/asyncHandler.util');

const router = require('express').Router();

// This router has been checked for the access through role.route.js

router.get('',
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.getPermissionGrantList)
);
router.get('/:id',
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.getGrantsByRole)
);

router.patch("/:id",
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.addNewGrantsToRole)
);

module.exports = router;