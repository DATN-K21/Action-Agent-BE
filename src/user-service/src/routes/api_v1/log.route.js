const router = require('express').Router();
const LogHelper = require('../../helpers/log.helper');
const handleAsync = require('../../utils/asyncHandler.util');


router.post('/', handleAsync(LogHelper.pushLog));

module.exports = router;