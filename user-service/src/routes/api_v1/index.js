const router = require('express').Router();

router.use('/log', require('./log.route'));
router.use('/user', require('./user.route'));
router.use('/access', require('./access.route'));
router.use('/resource', require('./resource.route'));
router.use('/role', require('./role.route'));
router.use('/profile', require('./profile.route'));
router.use('/subsystem', require('./subsystem.route'));

module.exports = router;