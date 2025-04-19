
const privateEndpointMiddleware = async (req, res, next) => {
    if (req.path.match(/^\/[^/]+\/private/)) {
        return res.sendStatus(403);
    }
    next();
};

module.exports = privateEndpointMiddleware;