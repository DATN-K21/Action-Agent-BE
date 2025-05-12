const router = require('express').Router();
const AccessMiddleware = require('../../middlewares/access.middleware');
const resourceController = require('../../modules/resource/resource.controller');
const handleAsync = require('../../utils/asyncHandler.util');
const permissionMiddleware = require('../../middlewares/permission.middleware');

router.use(handleAsync(AccessMiddleware.checkAccess));

// Other SUP-ROUTES imported here
// For example: router.use('/avatar', require('./avatar.route'));





// IMPORTANT: Common routes middleware, sup-routes imported ABOVE this line
router.use((req, res, next) => {
    const id = req.path.split("/")[1];
    req.params.id = id;

    handleAsync(permissionMiddleware.checkPermission("Resource", resourceController.getResourceOwnerIds))(req, res, next);
});

router.get('/', handleAsync(resourceController.getResourceList));
router.get('/:id', handleAsync(resourceController.getResourceById));

router.post("/", handleAsync(resourceController.createNewResource));

router.patch("/:id", handleAsync(resourceController.updateResource));

router.delete("/:id", handleAsync(resourceController.deleteResource));

module.exports = router;