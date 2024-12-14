const router = require('express').Router();
const AccessMiddleware = require('../../middlewares/access.middleware');
const resourceController = require('../../modules/resource/resource.controller');
const handleAsync = require('../../utils/asyncHandler.util');
const PermissionMiddleware = require('../../middlewares/permission.middleware');
const permissionMiddleware = require('../../middlewares/permission.middleware');

router.use(handleAsync(AccessMiddleware.checkAccess));

router.get('/',
    handleAsync(permissionMiddleware.checkPermission("Resource", resourceController.getResourceOwnerIds)),
    handleAsync(resourceController.getResourceList)
);
router.get('/:id',
    handleAsync(permissionMiddleware.checkPermission("Resource", resourceController.getResourceOwnerIds)),
    handleAsync(resourceController.getResourceById)
);

router.post("/",
    handleAsync(permissionMiddleware.checkPermission("Resource", resourceController.getResourceOwnerIds)),
    handleAsync(resourceController.createNewResource)
);

router.patch("/:id",
    handleAsync(permissionMiddleware.checkPermission("Resource", resourceController.getResourceOwnerIds)),
    handleAsync(resourceController.updateResource)
);

router.delete("/:id",
    handleAsync(permissionMiddleware.checkPermission("Resource", resourceController.getResourceOwnerIds)),
    handleAsync(resourceController.deleteResource)
);

module.exports = router;