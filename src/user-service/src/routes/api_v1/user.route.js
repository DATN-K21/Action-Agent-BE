const AccessMiddleware = require('../../middlewares/access.middleware');
const permissionMiddleware = require('../../middlewares/permission.middleware');
const userController = require('../../modules/user/user.controller');
const handleAsync = require('../../utils/asyncHandler.util');

const router = require('express').Router();

router.use(handleAsync(AccessMiddleware.checkAccess));

// Other SUP-ROUTES imported here
// For example: router.use('/avatar', require('./avatar.route'));





// IMPORTANT: Common routes middleware, sup-routes imported ABOVE this line
router.use((req, res, next) => {
	const id = req.path.split("/")[1];
	req.params.id = id;

	handleAsync(permissionMiddleware.checkPermission("User", userController.getUserOwnerIds))(req, res, next);
})


router.get("/", handleAsync(userController.getUserList));
router.get("/me", handleAsync(userController.getCurrentUser));
router.get("/current", handleAsync((req, res) => {
	const id = req.headers['x-user-id'];
	const email = req.headers['x-user-email'];
	const role = req.headers['x-user-role'];
	if (!id || !email || !role) {
		return res.status(401).json({
			message: 'Unauthorized',
			data: { id, email, role }
		});
	}
	return res.status(200).json({
		message: 'Current user',
		data: { id, email, role }
	});
}));
router.get("/:id", handleAsync(userController.getUserById));

router.post("/", handleAsync(userController.createNewUser));

router.patch("/:id", handleAsync(userController.updateUser));

router.delete("/:id", handleAsync(userController.deleteUser));

module.exports = router;