const ENDPOINT_CONFIGS = require('../configs/endpoint.config');

class UserUtil {
  static USER_HEADER_REQUIRED_REQUEST_PATHS = [
    `/api/user/api/v1/user/current`,
  ]

  static checkIfUserHeaderIsRequired(path) {
    return this.USER_HEADER_REQUIRED_REQUEST_PATHS.includes(path);
  }
}

module.exports = UserUtil;