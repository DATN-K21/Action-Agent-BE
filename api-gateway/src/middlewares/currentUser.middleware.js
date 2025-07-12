
const axiosInstance = require('../configs/axios.config');
const ENDPOINT_CONFIGS = require('../configs/endpoint.config');

const PUBLIC_ENDPOINTS = [
  // Ping endpoints
  "/",
  "/ping",
  "user/ping",
  "ai/ping",
  "extension/ping",
  "voice/ping",
  "payment/ping",

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
]

const currentUserMiddleware = async (req, res, next) => {
  req.headers['x-user-id'] = "";
  req.headers['x-user-email'] = "";
  req.headers['x-user-role'] = "";

  if (PUBLIC_ENDPOINTS.includes(req.path)) {
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

  try {
    const response = await axiosInstance.get(`${ENDPOINT_CONFIGS.USER_SERVICE_URL}/api/v1/user/me`, {
      headers: { Authorization: authHeader, 'x-client-id': req.headers['x-client-id'] },
    });

    const userData = response.data;
    req.headers['x-user-id'] = userData.id ?? "";
    req.headers['x-user-email'] = userData.email ?? "";
    req.headers['x-user-role'] = userData.role ?? "";

    next();
  } catch (error) {
    console.error('Failed to get current user data: ', error);
    if (error.status && error?.message && error?.errorStack) {
      const sanitizedError = { ...error };
      if (process.env.NODE_ENV !== "development") {
        delete sanitizedError.errorStack; // Remove sensitive information
      }
      res.status(error.status).json(sanitizedError);
    } else {
      res.status(500).json({ error: `Failed to get current user data.` });
    }
  }
};

module.exports = currentUserMiddleware;