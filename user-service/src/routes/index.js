const router = require('express').Router();


router.get('/', (req, res) => {
    res.render('index');
});

router.get("/health", (req, res) => {
    res.status(200).json({ status: "UP" });
});

router.use('/api/v1/', require('./api_v1/index'))

module.exports = router;