const router = require('express').Router();
// const ApiKeyMiddleware = require('../middlewares/apiKey.middleware');

// router.use(ApiKeyMiddleware.validateApiKey);

router.use('/api/v1', require('./api.route'));

module.exports = router;
