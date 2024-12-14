const router = require('express').Router();
const AccessMiddleware = require("../../middlewares/access.middleware");
const permissionMiddleware = require("../../middlewares/permission.middleware");
const userController = require("../../modules/user/user.controller");
const subSystemController = require("../../modules/subsystem_manage/subsystem.controller");
const handleAsync = require('../../utils/asyncHandler.util');

router.use(handleAsync(AccessMiddleware.checkAccess));

router.get("/",
    handleAsync(permissionMiddleware.checkPermission("SubSystem", userController.getUserOwnerIds)),
    handleAsync(subSystemController.getSubSystemList)
);
router.get("/:id",
    handleAsync(permissionMiddleware.checkPermission("SubSystem", userController.getUserOwnerIds)),
    handleAsync(subSystemController.getSubSystemById)
);

router.post("/",
    handleAsync(permissionMiddleware.checkPermission("SubSystem", userController.getUserOwnerIds)),
    handleAsync(subSystemController.createNewSubSystem)
);

router.patch("/:id",
    handleAsync(permissionMiddleware.checkPermission("SubSystem", userController.getUserOwnerIds)),
    handleAsync(subSystemController.updateSubSystem)
);

router.delete("/:id",
    handleAsync(permissionMiddleware.checkPermission("SubSystem", userController.getUserOwnerIds)),
    handleAsync(subSystemController.deleteSubSystem)
);

module.exports = router;