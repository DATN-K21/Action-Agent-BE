const handleAsync = require('../../utils/asyncHandler.util');
const AccessMiddleware = require("../../middlewares/access.middleware");
const profileController = require('../../modules/profile/profile.controller');
const permissionMiddleware = require('../../middlewares/permission.middleware');
const router = require('express').Router();

router.use(handleAsync(AccessMiddleware.checkAccess));

// Other SUP-ROUTES imported here
// For example: router.use('/avatar', require('./avatar.route'));





// IMPORTANT: Common routes middleware, sup-routes imported ABOVE this line
router.use((req, res, next) => {
    const id = req.path.split("/")[1];
    req.params.id = id;

    handleAsync(permissionMiddleware.checkPermission("Profile", profileController.getProfileOwnerIds))(req, res, next);
});

router.get("/", handleAsync(profileController.getProfileList));
router.get("/:id", handleAsync(profileController.getProfileById));

router.post("/", handleAsync(profileController.createNewProfile));

router.patch("/:id", handleAsync(profileController.updateProfile));

router.delete("/:id", handleAsync(profileController.deleteProfile));

module.exports = router;