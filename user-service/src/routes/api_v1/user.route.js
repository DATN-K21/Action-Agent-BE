const AccessMiddleware = require('../../middlewares/access.middleware');
const permissionMiddleware = require('../../middlewares/permission.middleware');
const userController = require('../../modules/user/user.controller');
const handleAsync = require('../../utils/asyncHandler.util');

const router = require('express').Router();

router.use(handleAsync(AccessMiddleware.checkAccess));

router.get("/",
    handleAsync(permissionMiddleware.checkPermission("User", userController.getUserOwnerIds)),
    handleAsync(userController.getUserList)
);
router.get("/:id",
    handleAsync(permissionMiddleware.checkPermission("User", userController.getUserOwnerIds)),
    handleAsync(userController.getUserById)
);

router.post("/",
    handleAsync(permissionMiddleware.checkPermission("User", userController.getUserOwnerIds)),
    handleAsync(userController.createNewUser)
);

router.patch("/:id",
    handleAsync(permissionMiddleware.checkPermission("User", userController.getUserOwnerIds)),
    handleAsync(userController.updateUser)
);

router.delete("/:id",
    handleAsync(permissionMiddleware.checkPermission("User", userController.getUserOwnerIds)),
    handleAsync(userController.deleteUser)
);

module.exports = router;