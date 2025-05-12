const router = require('express').Router();

router.get("/ping", (req, res) => {
    res.status(200).json({ message: "pong" });
});

router.use('/api/v1/', require('./api_v1/index'))

module.exports = router;