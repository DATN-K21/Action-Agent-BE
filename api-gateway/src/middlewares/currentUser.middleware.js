
const axiosInstance = require('../configs/axios.config');
const ENDPOINT_CONFIGS = require('../configs/endpoint.config');
const globalUserCache = require('../utils/userCache.utils');

const PUBLIC_ENDPOINTS = [
  // Ping endpoints
  "/",
  "/ping",
  "/user/ping",
  "/ai/ping",
  "/extension/ping",
  "/voice/ping",
  "/payment/ping",

  // User service public endpoints
  "/user/api/v1/access/login",
  "/user/api/v1/access/signup",
  "/user/api/v1/access/forgot-password",
  "/user/api/v1/access/invoke-new-tokens",
  "/user/api/v1/access/activate/send-link",
  "/user/api/v1/access/activate/confirm",
  "/user/api/v1/access/google/auth",
  "/user/api/v1/access/facebook/auth",
  "/user/api/v1/access/facebook/verify",
  "/user/api/v1/access/reset-password/send-otp",
  "/user/api/v1/access/reset-password/confirm-otp",
  "/user/api/v1/access/reset-password",

  // Payment service public endpoints
  "/payment/api/v1/payment/confirm",

  // AI service public endpoints
  "/ai/api/v1/callback/extension/*"
]

const currentUserMiddleware = async (req, res, next) => {
  req.headers['x-user-id'] = null;
  req.headers['x-user-email'] = null;
  req.headers['x-user-role'] = null;

  if (PUBLIC_ENDPOINTS.includes(req.path)|| req.path.startsWith('/ai/api/v1/callback/extension')) {
    console.log(`Skip auth middleware public endpoint: ${req.path}`);
    return next();
  }

  const authHeader = req.headers.authorization;
  if (!authHeader) {
    console.error('Authorization header is missing!');
    return res.status(401).json({
      status: 401,
      message: 'Authorization header is required.',
      data: null,
    });
  }
  const authUserKey = authHeader.split(' ')[1];
  if (!authUserKey) {
    return res.status(401).json({
      status: 401,
      message: 'Invalid authorization header format.',
      data: null,
    });
  }

  
  try {
    const cachedUserData = globalUserCache.get(authUserKey);
    if (cachedUserData && cachedUserData.id && cachedUserData.email && cachedUserData.role) {
      setAuthHeaderFromData(req, cachedUserData);
      return next();
    }

    const response = await axiosInstance.get(`${ENDPOINT_CONFIGS.USER_SERVICE_URL}/api/v1/user/me`, {
      headers: { Authorization: authHeader },
    });

    const userData = response.data;
    if(!userData || !userData.id || !userData.email || !userData.role) {
      return res.status(400).json({
        status: 400,
        message: 'Invalid user data received from service.',
        data: null,
      });
    } else {
      setAuthHeaderFromData(req, {
        id: userData.id,
        email: userData.email,
        role: userData.role,
      })
    }

    globalUserCache.set(authUserKey, {
      id: userData.id,
      email: userData.email,
      role: userData.role,
    });

    next();
  } catch (error) {
    console.error('Failed to get current user data: ', error);
    // Delete cache for unauthorized access
    if (error.response && [401, 403].includes(+error.response.status)) {
      globalUserCache.delete(authUserKey);
    }

    // Handle error response
    // Delete cache for unauthorized access
    if (error.response && [401, 403].includes(+error.response.status)) {
      globalUserCache.delete(authUserKey);
    }

    // Handle error response
    if (error.status && error?.message && error?.errorStack) {
      const sanitizedError = { ...error };
      if (process.env.NODE_ENV !== "development") {
        delete sanitizedError.errorStack; // Remove sensitive information
      }
      res.status(error.status).json(sanitizedError);
    } else {
      res.status(500).json({ error: `Failed to get current user data: ${error.message}` });
    }
  }
};

const setAuthHeaderFromData = (req, data = {}) => {
  const {  id, email, role } = data;
  if (!id || !email || !role) {
    throw new Error("Invalid user data provided");
  }
  req.headers['x-user-id'] = id;
  req.headers['x-user-email'] = email;
  req.headers['x-user-role'] = role;
};

module.exports = currentUserMiddleware;