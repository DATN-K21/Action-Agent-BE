const AccessController = require('../../modules/access/access.controller');
const handleAsync = require('../../utils/asyncHandler.util');
const passport = require('passport');
const AccessMiddleware = require('../../middlewares/access.middleware');

const router = require('express').Router();

router.post("/signup", handleAsync(AccessController.handleSignup));
router.post("/login", handleAsync(AccessController.handleLogin));
router.post("/verify/send-otp", handleAsync(AccessController.handleVerifyEmail));
router.post("/verify/confirm-otp", handleAsync(AccessController.handleVerifyOTP));

//New activate method
router.post("/activate/send-link", handleAsync(AccessController.handleSendLinkToActivateAccount));
router.get("/activate", handleAsync(AccessController.handleActivateAccount));

router.post('/google/auth', handleAsync(AccessController.handleLoginWithGoogle));

router.get('/facebook/auth', passport.authenticate('facebook'));

router.get('/facebook/verify',
    passport.authenticate('facebook', { session: false, failureRedirect: '/' }),
    handleAsync(AccessController.handleLoginWithFacebook)
);

router.post("/reset-password/send-otp", handleAsync(AccessController.handleSendOTPToResetPassword));
router.post("/reset-password/confirm-otp", handleAsync(AccessController.handleConfirmOTPToResetPassword))
router.post("/reset-password", handleAsync(AccessController.handleResetPassword));

// Check access
router.use(handleAsync(AccessMiddleware.checkAccess))

router.post("/invoke-new-tokens", handleAsync(AccessController.handleInvokeNewTokens));
router.post("/logout", handleAsync(AccessController.handleLogout));

module.exports = router;