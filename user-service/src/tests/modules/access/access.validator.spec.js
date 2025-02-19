const AccessValidator = require("../../../modules/access/access.validator")
const {
	validSignupPayload,
	validLoginPayload,
	validInvokeNewTokenRequest,
	validInvokeNewTokenResult,
	validateResetPasswordRequest,
	validResetPasswordResult,
	validVerifyOTPPayload,
	validVerifyOTPResult,
	validLogoutRequest,
} = require("./access.mock")

describe('AccessValidator', () => {
	beforeEach(() => {
		jest.clearAllMocks()
		jest.resetAllMocks()
	})

	describe('validateSignup', () => {
		it('should validate sign up successfully', async () => {
			const req = { body: validSignupPayload };
			const result = AccessValidator.validateSignup(req)

			expect(result).toEqual({
				error: false,
				data: validSignupPayload
			})
		})

		it('should validate sign up with empty email', async () => {
			const req = { body: { ...validSignupPayload, email: '' } }
			const result = AccessValidator.validateSignup(req)

			expect(result).toEqual({
				error: true,
				code: 1010101,
				message: 'Email is required'
			})
		})

		it('should validate sign up with invalid email', async () => {
			const req = { body: { ...validSignupPayload, email: 'invalid-email' } }
			const result = AccessValidator.validateSignup(req)

			expect(result).toEqual({
				error: true,
				code: 1010102,
				message: 'Invalid email format'
			})
		})

		it('should validate sign up with empty password', async () => {
			const req = { body: { ...validSignupPayload, password: '' } }
			const result = AccessValidator.validateSignup(req)

			expect(result).toEqual({
				error: true,
				code: 1010103,
				message: 'Password is required'
			})
		})

		it('should validate sign up with password less than 3 characters', async () => {
			const req = { body: { ...validSignupPayload, password: '12' } }
			const result = AccessValidator.validateSignup(req)

			expect(result).toEqual({
				error: true,
				code: 1010104,
				message: 'Password must be at least 3 characters long'
			})
		})
	});

	describe('validateLogin', () => {
		it('should validate login successfully', async () => {
			const req = { body: validLoginPayload };
			const result = AccessValidator.validateLogin(req)

			expect(result).toEqual({
				error: false,
				data: validLoginPayload
			})
		});

		it('should validate login with empty email', async () => {
			const req = { body: { ...validLoginPayload, email: '' } }
			const result = AccessValidator.validateLogin(req)

			expect(result).toEqual({
				error: true,
				code: 1010201,
				message: 'Email is required'
			})
		});

		it('should validate login with invalid email', async () => {
			const req = { body: { ...validLoginPayload, email: 'invalid-email' } }
			const result = AccessValidator.validateLogin(req)

			expect(result).toEqual({
				error: true,
				code: 1010202,
				message: 'Invalid email format'
			})
		});

		it('should validate login with empty password', async () => {
			const req = { body: { ...validLoginPayload, password: '' } }
			const result = AccessValidator.validateLogin(req)

			expect(result).toEqual({
				error: true,
				code: 1010203,
				message: 'Password is required'
			})
		});

		it('should validate login with password less than 3 characters', async () => {
			const req = { body: { ...validLoginPayload, password: '12' } }
			const result = AccessValidator.validateLogin(req)

			expect(result).toEqual({
				error: true,
				code: 1010204,
				message: 'Password must be at least 3 characters long'
			})
		});
	});

	describe('validateInvokeNewToken', () => {
		it('should validate invoke new token successfully', async () => {
			const req = { ...validInvokeNewTokenRequest };
			const result = AccessValidator.validateInvokeNewToken(req);

			expect(result).toEqual(validInvokeNewTokenResult);
		});

		it('should validate invoke new token with empty client ID', async () => {
			const req = { ...validInvokeNewTokenRequest, headers: { ...validInvokeNewTokenRequest.headers, 'x-client-id': '' } };
			const result = AccessValidator.validateInvokeNewToken(req);

			expect(result).toEqual({
				error: true,
				code: 1010301,
				message: 'Client ID is required'
			});
		});

		it('should validate invoke new token with empty access token', async () => {
			const req = { ...validInvokeNewTokenRequest, headers: { ...validInvokeNewTokenRequest.headers, 'authorization': '' } };
			const result = AccessValidator.validateInvokeNewToken(req);

			expect(result).toEqual({
				error: true,
				code: 1010302,
				message: 'Authentication credential is required'
			});
		});

		it('should validate invoke new token with invalid access token', async () => {
			const req = { ...validInvokeNewTokenRequest, headers: { ...validInvokeNewTokenRequest.headers, 'authorization': 'invalid-access-token' } };
			const result = AccessValidator.validateInvokeNewToken(req);

			expect(result).toEqual({
				error: true,
				code: 1010303,
				message: 'Unauthorized'
			});
		});

		it('should validate invoke new token with empty refresh token', async () => {
			const req = { ...validInvokeNewTokenRequest, body: { ...validInvokeNewTokenRequest.body, refreshToken: '' } };
			const result = AccessValidator.validateInvokeNewToken(req);

			expect(result).toEqual({
				error: true,
				code: 1010304,
				message: 'Refresh token is required'
			});
		});
	})

	describe('validateResetPassword', () => {
		it('should validate reset password successfully', async () => {
			const req = { ...validateResetPasswordRequest };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual(validResetPasswordResult);
		});

		it('should validate reset password with empty client ID', async () => {
			const req = { ...validateResetPasswordRequest, headers: { ...validateResetPasswordRequest.headers, 'x-client-id': '' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011401,
				message: 'Client ID is required'
			});
		});

		it('should validate reset password with empty access token', async () => {
			const req = { ...validateResetPasswordRequest, headers: { ...validateResetPasswordRequest.headers, 'authorization': '' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011402,
				message: 'Authentication credential is required'
			});
		});

		it('should validate reset password with invalid access token', async () => {
			const req = { ...validateResetPasswordRequest, headers: { ...validateResetPasswordRequest.headers, 'authorization': 'invalid-access-token' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011403,
				message: 'Unauthorized'
			});
		});

		it('should validate reset password with empty new password', async () => {
			const req = { ...validateResetPasswordRequest, body: { ...validateResetPasswordRequest.body, newPassword: '' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011404,
				message: 'Password is required'
			});
		});

		it('should validate reset password with password less than 3 characters', async () => {
			const req = { ...validateResetPasswordRequest, body: { ...validateResetPasswordRequest.body, newPassword: '12' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011405,
				message: 'Password must be at least 3 characters long'
			});
		});

		it('should validate reset password with empty confirm password', async () => {
			const req = { ...validateResetPasswordRequest, body: { ...validateResetPasswordRequest.body, confirmNewPassword: '' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011406,
				message: 'Confirm password is required'
			});
		});

		it('should validate reset password with password does not match', async () => {
			const req = { ...validateResetPasswordRequest, body: { ...validateResetPasswordRequest.body, confirmNewPassword: 'not-match' } };
			const result = AccessValidator.validateResetPassword(req);

			expect(result).toEqual({
				error: true,
				code: 1011407,
				message: 'Password does not match'
			});
		});
	})

	describe('validateVerifyEmail', () => {
		it('should validate verify email successfully', async () => {
			const req = { body: { email: "jest@tester.com" } };
			const result = await AccessValidator.validateVerifyEmail(req);

			expect(result).toEqual({
				error: false,
				data: {
					userEmail: req.body.email
				}
			});
		});

		it('should validate verify email with empty email', async () => {
			const req = { body: { email: "" } };
			const result = await AccessValidator.validateVerifyEmail(req);

			expect(result).toEqual({
				error: true,
				code: 1010401,
				message: 'Email is required'
			});
		});

		it('should validate verify email with invalid email', async () => {
			const req = { body: { email: "invalid-email" } };
			const result = await AccessValidator.validateVerifyEmail(req);

			expect(result).toEqual({
				error: true,
				code: 1010402,
				message: 'Invalid email format'
			});
		});
	});

	describe('validateVerifyOTP', () => {
		it('should validate verify OTP successfully', async () => {
			const req = { body: validVerifyOTPPayload };
			const result = await AccessValidator.validateVerifyOTP(req);

			expect(result).toEqual(validVerifyOTPResult);
		});

		it('should validate verify OTP with empty email', async () => {
			const req = { body: { ...validVerifyOTPPayload, email: '' } };
			const result = await AccessValidator.validateVerifyOTP(req);

			expect(result).toEqual({
				error: true,
				code: 1010501,
				message: 'Email is required'
			});
		});

		it('should validate verify OTP with invalid email', async () => {
			const req = { body: { ...validVerifyOTPPayload, email: 'invalid-email' } };
			const result = await AccessValidator.validateVerifyOTP(req);

			expect(result).toEqual({
				error: true,
				code: 1010502,
				message: 'Invalid email format'
			});
		});

		it('should validate verify OTP with empty OTP', async () => {
			const req = { body: { ...validVerifyOTPPayload, otp: '' } };
			const result = await AccessValidator.validateVerifyOTP(req);

			expect(result).toEqual({
				error: true,
				code: 1010503,
				message: 'OTP is required'
			});
		});

		it('should validate verify OTP with OTP whose length is not 6 characters', async () => {
			const req = { body: { ...validVerifyOTPPayload, otp: '12345' } };
			const result = await AccessValidator.validateVerifyOTP(req);

			expect(result).toEqual({
				error: true,
				code: 1010504,
				message: 'OTP must be 6 characters long'
			});
		});
	});

	describe('validateGoogleLogin', () => {
		it('should validate google login successfully', async () => {
			const req = { body: { id_token: 'jest-id-token' } };
			const result = AccessValidator.validateGoogleLogin(req);

			expect(result).toEqual({
				error: false,
				data: {
					idToken: req.body.id_token
				}
			});
		});

		it('should validate google login with empty id token', async () => {
			const req = { body: { id_token: '' } };
			const result = AccessValidator.validateGoogleLogin(req);

			expect(result).toEqual({
				error: true,
				code: 1010601,
				message: 'Google ID Token not found'
			});
		});
	});

	describe('validateFacebookLogin', () => {
		it('should validate facebook login successfully', async () => {
			const profile = { displayName: 'jest-display-name', id: 'jest-facebook-id' };
			const result = AccessValidator.validateFacebookLogin(profile);

			expect(result).toEqual({
				error: false,
				data: {
					username: profile.displayName,
					facebook_id: profile.id,
					type_login: 'facebook'
				}
			});
		});

		it('should validate facebook login with empty display name', async () => {
			const profile = { displayName: '', id: 'jest-facebook-id' };
			const result = AccessValidator.validateFacebookLogin(profile);

			expect(result).toEqual({
				error: true,
				code: 1010903,
				message: 'Display name not found'
			});
		});
	});

	describe('validateLogout', () => {
		it('should validate logout successfully', async () => {
			const req = { ...validLogoutRequest };
			const result = AccessValidator.validateLogout(req);

			expect(result).toEqual({
				error: false,
				data: { user: { id: req.user.id } }
			});
		});

		it('should validate logout with empty client ID', async () => {
			const req = { ...validLogoutRequest, user: { id: '' } };
			const result = AccessValidator.validateLogout(req);

			expect(result).toEqual({
				error: true,
				code: 1011001,
				message: 'Unauthorized'
			});
		});
	})
})