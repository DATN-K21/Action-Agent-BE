const router = require('express').Router();
const AccessMiddleware = require('../../middlewares/access.middleware');
const permissionMiddleware = require('../../middlewares/permission.middleware');
const roleController = require('../../modules/role/role.controller');
const handleAsync = require('../../utils/asyncHandler.util');

// MIDDLEWARES
router.use(handleAsync(AccessMiddleware.checkAccess));

// SUB ROUTES
// Other SUP-ROUTES imported here
// For example: router.use('/avatar', require('./avatar.route'));
router.use("/grant", require('./role.grant.route'));



// IMPORTANT: Common routes middleware, sup-routes imported ABOVE this line
router.use((req, res, next) => {
    const id = req.path.split("/")[1];
    req.params.id = id;

    handleAsync(permissionMiddleware.checkPermission("Role", roleController.getRoleOwnerIds))(req, res, next);
})

// ROUTES
router.get('/', handleAsync(roleController.getRoleList));
router.get('/:id', handleAsync(roleController.getRoleById));

router.post("/", handleAsync(roleController.createNewRole));

router.patch("/:id", handleAsync(roleController.updateRole));

router.delete("/:id", handleAsync(roleController.deleteRole));

module.exports = router;