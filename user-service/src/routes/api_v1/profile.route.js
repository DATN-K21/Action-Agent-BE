const handleAsync = require('../../utils/asyncHandler.util');
const AccessMiddleware = require("../../middlewares/access.middleware");
const profileController = require('../../modules/profile/profile.controller');
const permissionMiddleware = require('../../middlewares/permission.middleware');
const router = require('express').Router();

router.use(handleAsync(AccessMiddleware.checkAccess));

router.get("/",
    handleAsync(permissionMiddleware.checkPermission("Profile", profileController.getProfileOwnerIds)),
    handleAsync(profileController.getProfileList)
);
router.get("/:id",
    handleAsync(permissionMiddleware.checkPermission("Profile", profileController.getProfileOwnerIds)),
    handleAsync(profileController.getProfileById)
);

router.post("/",
    handleAsync(permissionMiddleware.checkPermission("Profile", profileController.getProfileOwnerIds)),
    handleAsync(profileController.createNewProfile)
);

router.patch("/:id",
    handleAsync(permissionMiddleware.checkPermission("Profile", profileController.getProfileOwnerIds)),
    handleAsync(profileController.updateProfile)
);

router.delete("/:id",
    handleAsync(permissionMiddleware.checkPermission("Profile", profileController.getProfileOwnerIds)),
    handleAsync(profileController.deleteProfile)
);

module.exports = router;