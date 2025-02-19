const router = require('express').Router();


router.get('/', (req, res) => {
    res.render('index');
});

router.use('/api/v1/', require('./api_v1/index'))

module.exports = router;