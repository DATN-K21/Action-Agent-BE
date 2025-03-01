
const axiosInstance = require('../configs/axios.config');
const ENDPOINT_CONFIGS = require('../configs/endpoint.config');
const UserUtil = require('../utils/user.utils');

const currentUserMiddleware = async (req, res, next) => {
  const authHeader = req.headers.authorization;
  const userServiceUrl = ENDPOINT_CONFIGS.USER_SERVICE_URL;
  if (authHeader && UserUtil.checkIfUserHeaderIsRequired(req.originalUrl)) {
    try {
      const response = await axiosInstance.get(`${userServiceUrl}/api/v1/user/me`, {
        headers: { Authorization: authHeader, 'x-client-id': req.headers['x-client-id'] },
      });

      const userData = response.data;
      req.headers['x-user-id'] = userData.id ?? "";
      req.headers['x-user-email'] = userData.email ?? "";
      req.headers['x-user-role'] = userData.role ?? "";

      next();
    } catch (error) {
      console.error('Failed to get current user data: ', error.message);
      if (error.status && error?.code && error?.message && error?.errorStack) {
        res.status(error.status).json({ ...error, errorStack: undefined });
      } else {
        res.status(500).json({ error: `Failed to get current user data.` });
      }
    }
  } else {
    next();
  }
};

module.exports = currentUserMiddleware;