const router = require('express').Router();
const AccessMiddleware = require("../../middlewares/access.middleware");
const permissionMiddleware = require("../../middlewares/permission.middleware");
const userController = require("../../modules/user/user.controller");
const subSystemController = require("../../modules/subsystem_manage/subsystem.controller");
const handleAsync = require('../../utils/asyncHandler.util');

router.use(handleAsync(AccessMiddleware.checkAccess));

// Other SUP-ROUTES imported here
// For example: router.use('/avatar', require('./avatar.route'));





// IMPORTANT: Common routes middleware, sup-routes imported ABOVE this line
router.use((req, res, next) => {
    const id = req.path.split("/")[1];
    req.params.id = id;

    handleAsync(permissionMiddleware.checkPermission("SubSystem", userController.getUserOwnerIds))(req, res, next);
})

router.get("/", handleAsync(subSystemController.getSubSystemList));
router.get("/:id", handleAsync(subSystemController.getSubSystemById));

router.post("/", handleAsync(subSystemController.createNewSubSystem));

router.patch("/:id", handleAsync(subSystemController.updateSubSystem));

router.delete("/:id", handleAsync(subSystemController.deleteSubSystem));

module.exports = router;