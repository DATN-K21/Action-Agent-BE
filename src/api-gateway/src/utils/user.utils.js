const ENDPOINT_CONFIGS = require('../configs/endpoint.config');

class UserUtil {
  static USER_HEADER_REQUIRED_REQUEST_PATHS = [
    `/user/api/v1/user/current`,
  ]

  static checkIfUserHeaderIsRequired(path) {
    return (path.includes(ENDPOINT_CONFIGS.AI_SERVICE_URL) || this.USER_HEADER_REQUIRED_REQUEST_PATHS.includes(path));
  }
}

module.exports = UserUtil;