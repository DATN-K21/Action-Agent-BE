const router = require('express').Router();
const AccessMiddleware = require('../../middlewares/access.middleware');
const permissionMiddleware = require('../../middlewares/permission.middleware');
const roleController = require('../../modules/role/role.controller');
const handleAsync = require('../../utils/asyncHandler.util');

// MIDDLEWARES
router.use(handleAsync(AccessMiddleware.checkAccess));

// SUB ROUTES
router.use("/grant", require('./role.grant.route'));

// ROUTES
router.get('/',
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.getRoleList)
);
router.get('/:id',
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.getRoleById)
);

router.post("/",
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.createNewRole)
);

router.patch("/:id",
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.updateRole)
);

router.delete("/:id",
    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds)),
    handleAsync(roleController.deleteRole)
);

module.exports = router;