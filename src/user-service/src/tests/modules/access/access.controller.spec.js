const AccessService = require('../../../modules/access/access.service');
const AccessValidator = require('../../../modules/access/access.validator');
const AccessController = require('../../../modules/access/access.controller');
const { BadRequestResponse } = require("../../../response/error");
const { MongooseError } = require("mongoose");

const {
	validGetAccessOwnerIdsRequest,
	validGetAccessOwnerIdsResult,
	validSignupPayload,
	validSignupResult,
	validLoginPayload,
	validLoginResult,
	validInvokeNewTokenRequest,
	validInvokeNewTokenResult,
	validVerifyEmailPayload,
	validVerifyEmailResult,
	validVerifyOTPPayload,
	validVerifyOTPResult,
	validateResetPasswordRequest,
	validResetPasswordResult,
	validLogoutRequest,
} = require('./access.mock');

jest.mock('../../../modules/access/access.service');
jest.mock('../../../modules/access/access.validator');

describe('AccessController', () => {
	let accessService;
	let res;

	beforeEach(() => {
		accessService = new AccessService();
		AccessController.accessService = accessService;

		res = {
			status: jest.fn().mockReturnThis(),
			json: jest.fn(),
		};
	});

	afterEach(() => {
		jest.resetAllMocks();
	});

	describe('getAccessOwnerIds', () => {
		const req = validGetAccessOwnerIdsRequest;

		it('should get access owner ids successfully', async () => {
			accessService.getAccessById.mockResolvedValue(validGetAccessOwnerIdsResult);

			const result = await AccessController.getAccessOwnerIds(req, res);

			expect(accessService.getAccessById).toHaveBeenCalled();
			expect(result).toEqual(validGetAccessOwnerIdsResult.owners);
		});

		it('should return empty array if no params id is provided', async () => {
			const newReq = { params: {} };

			const result = await AccessController.getAccessOwnerIds(newReq, res);

			expect(accessService.getAccessById).not.toHaveBeenCalled();
			expect(result).toEqual([]);
		});

		it('should throw MongooseError if a MongooseError is occurred', async () => {
			accessService.getAccessById.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.getAccessOwnerIds(req, res);
			} catch (error) {
				expect(accessService.getAccessById).toHaveBeenCalled();
				expect(error).toBeInstanceOf(MongooseError);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			accessService.getAccessById.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.getAccessOwnerIds(req, res);
			} catch (error) {
				expect(accessService.getAccessById).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleSignup', () => {
		const req = { body: validSignupPayload };

		it('should signup successfully', async () => {
			AccessValidator.validateSignup.mockReturnValue({ data: req.body, error: false });
			accessService.handleSignup.mockResolvedValue(validSignupResult);

			await AccessController.handleSignup(req, res);

			expect(AccessValidator.validateSignup).toHaveBeenCalled();
			expect(accessService.handleSignup).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(201);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validSignupResult),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateSignup.mockReturnValue({ data: null, error: true });
			accessService.handleSignup.mockResolvedValue(validSignupResult);

			try {
				await AccessController.handleSignup(req, res);
			} catch (error) {
				expect(AccessValidator.validateSignup).toHaveBeenCalled();
				expect(accessService.handleSignup).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateSignup.mockReturnValue({ data: req.body, error: false });
			accessService.handleSignup.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleSignup(req, res);
			} catch (error) {
				expect(AccessValidator.validateSignup).toHaveBeenCalled();
				expect(accessService.handleSignup).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateSignup.mockReturnValue({ data: req.body, error: false });
			accessService.handleSignup.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleSignup(req, res);
			} catch (error) {
				expect(AccessValidator.validateSignup).toHaveBeenCalled();
				expect(accessService.handleSignup).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleLogin', () => {
		const req = { body: validLoginPayload };

		it('should login successfully', async () => {
			AccessValidator.validateLogin.mockReturnValue({ data: req.body, error: false });
			accessService.handleLogin.mockResolvedValue(validLoginResult);

			await AccessController.handleLogin(req, res);

			expect(AccessValidator.validateLogin).toHaveBeenCalled();
			expect(accessService.handleLogin).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validLoginResult),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateLogin.mockReturnValue({ data: null, error: true });
			accessService.handleLogin.mockResolvedValue(validLoginResult);

			try {
				await AccessController.handleLogin(req, res);
			} catch (error) {
				expect(AccessValidator.validateLogin).toHaveBeenCalled();
				expect(accessService.handleLogin).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateLogin.mockReturnValue({ data: req.body, error: false });
			accessService.handleLogin.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleLogin(req, res);
			} catch (error) {
				expect(AccessValidator.validateLogin).toHaveBeenCalled();
				expect(accessService.handleLogin).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateLogin.mockReturnValue({ data: req.body, error: false });
			accessService.handleLogin.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleLogin(req, res);
			} catch (error) {
				expect(AccessValidator.validateLogin).toHaveBeenCalled();
				expect(accessService.handleLogin).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleInvokeNewToken', () => {
		const req = validInvokeNewTokenRequest;

		it('should invoke new token successfully', async () => {
			AccessValidator.validateInvokeNewToken.mockReturnValue({ data: req.body, error: false });
			accessService.handleInvokeNewTokens.mockResolvedValue(validInvokeNewTokenResult.data);

			await AccessController.handleInvokeNewTokens(req, res);

			expect(accessService.handleInvokeNewTokens).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validInvokeNewTokenResult.data),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateInvokeNewToken.mockReturnValue({ data: null, error: true });
			accessService.handleInvokeNewTokens.mockResolvedValue(validInvokeNewTokenResult.data);

			try {
				await AccessController.handleInvokeNewTokens(req, res);
			} catch (error) {
				expect(AccessValidator.validateInvokeNewToken).toHaveBeenCalled();
				expect(accessService.handleInvokeNewTokens).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateInvokeNewToken.mockReturnValue({ data: req.body, error: false });
			accessService.handleInvokeNewTokens.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleInvokeNewTokens(req, res);
			} catch (error) {
				expect(AccessValidator.validateInvokeNewToken).toHaveBeenCalled();
				expect(accessService.handleInvokeNewTokens).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateInvokeNewToken.mockReturnValue({ data: req.body, error: false });
			accessService.handleInvokeNewTokens.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleInvokeNewTokens(req, res);
			} catch (error) {
				expect(AccessValidator.validateInvokeNewToken).toHaveBeenCalled();
				expect(accessService.handleInvokeNewTokens).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleVerifyEmail', () => {
		const req = { body: validVerifyEmailPayload };

		it('should verify email successfully', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: { userEmail: req.body.email }, error: false });
			accessService.sendOTPToVerifyEmail.mockResolvedValue(validVerifyEmailResult);

			await AccessController.handleVerifyEmail(req, res);

			expect(accessService.sendOTPToVerifyEmail).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining({ email: req.body.email }),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: null, error: true });
			accessService.sendOTPToVerifyEmail.mockResolvedValue(validVerifyEmailResult);

			try {
				await AccessController.handleVerifyEmail(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
				expect(accessService.sendOTPToVerifyEmail).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: { userEmail: req.body.email }, error: false });
			accessService.sendOTPToVerifyEmail.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleVerifyEmail(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
				expect(accessService.sendOTPToVerifyEmail).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: { userEmail: req.body.email }, error: false });
			accessService.sendOTPToVerifyEmail.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleVerifyEmail(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
				expect(accessService.sendOTPToVerifyEmail).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleVerifyOTP', () => {
		const req = { body: validVerifyOTPPayload };

		it('should verify OTP successfully', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: { ...req.body, userEmail: req.body.email }, error: false });
			accessService.verifyOTP.mockResolvedValue(validVerifyOTPResult.data);

			await AccessController.handleVerifyOTP(req, res);

			expect(accessService.verifyOTP).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validVerifyOTPResult.data),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: null, error: true });
			accessService.verifyOTP.mockResolvedValue(validVerifyOTPResult.data);

			try {
				await AccessController.handleVerifyOTP(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
				expect(accessService.verifyOTP).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: { ...req.body, userEmail: req.body.email }, error: false });
			accessService.verifyOTP.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleVerifyOTP(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
				expect(accessService.verifyOTP).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: { ...req.body, userEmail: req.body.email }, error: false });
			accessService.verifyOTP.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleVerifyOTP(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
				expect(accessService.verifyOTP).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleResetPassword', () => {
		const req = validateResetPasswordRequest;

		it('should reset password successfully', async () => {
			AccessValidator.validateResetPassword.mockReturnValue({ data: { ...req.body, userId: req.headers['x-client-id'] }, error: false });
			accessService.resetPassword.mockResolvedValue(validResetPasswordResult.data);

			await AccessController.handleResetPassword(req, res);

			expect(accessService.resetPassword).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validResetPasswordResult.data),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateResetPassword.mockReturnValue({ data: null, error: true });
			accessService.resetPassword.mockResolvedValue(validResetPasswordResult.data);

			try {
				await AccessController.handleResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateResetPassword).toHaveBeenCalled();
				expect(accessService.resetPassword).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateResetPassword.mockReturnValue({ data: { ...req.body, userId: req.headers['x-client-id'] }, error: false });
			accessService.resetPassword.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateResetPassword).toHaveBeenCalled();
				expect(accessService.resetPassword).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateResetPassword.mockReturnValue({ data: { ...req.body, userId: req.headers['x-client-id'] }, error: false });
			accessService.resetPassword.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateResetPassword).toHaveBeenCalled();
				expect(accessService.resetPassword).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleLogout', () => {
		const req = validLogoutRequest;

		it('should logout successfully', async () => {
			AccessValidator.validateLogout.mockReturnValue({ data: { user: req.user }, error: false });
			accessService.handleLogout.mockResolvedValue({});

			await AccessController.handleLogout(req, res);

			expect(accessService.handleLogout).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: {},
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateLogout.mockReturnValue({ data: null, error: true });
			accessService.handleLogout.mockResolvedValue({});

			try {
				await AccessController.handleLogout(req, res);
			} catch (error) {
				expect(AccessValidator.validateLogout).toHaveBeenCalled();
				expect(accessService.handleLogout).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateLogout.mockReturnValue({ data: { user: req.user }, error: false });
			accessService.handleLogout.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleLogout(req, res);
			} catch (error) {
				expect(AccessValidator.validateLogout).toHaveBeenCalled();
				expect(accessService.handleLogout).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateLogout.mockReturnValue({ data: { user: req.user }, error: false });
			accessService.handleLogout.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleLogout(req, res);
			} catch (error) {
				expect(AccessValidator.validateLogout).toHaveBeenCalled();
				expect(accessService.handleLogout).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleLoginWithGoogle', () => {
		const req = { body: { id_token: 'jest-id-token' } };

		it('should login with Google successfully', async () => {
			AccessValidator.validateGoogleLogin.mockReturnValue({ data: { idToken: req.body.id_token }, error: false });
			accessService.loginWithGoogle.mockResolvedValue(validLoginResult);

			await AccessController.handleLoginWithGoogle(req, res);

			expect(AccessValidator.validateGoogleLogin).toHaveBeenCalled();
			expect(accessService.loginWithGoogle).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validLoginResult),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateGoogleLogin.mockReturnValue({ data: null, error: true });
			accessService.loginWithGoogle.mockResolvedValue(validLoginResult);

			try {
				await AccessController.handleLoginWithGoogle(req, res);
			} catch (error) {
				expect(AccessValidator.validateGoogleLogin).toHaveBeenCalled();
				expect(accessService.loginWithGoogle).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateGoogleLogin.mockReturnValue({ data: { idToken: req.body.id_token }, error: false });
			accessService.loginWithGoogle.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleLoginWithGoogle(req, res);
			} catch (error) {
				expect(AccessValidator.validateGoogleLogin).toHaveBeenCalled();
				expect(accessService.loginWithGoogle).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateGoogleLogin.mockReturnValue({ data: { idToken: req.body.id_token }, error: false });
			accessService.loginWithGoogle.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleLoginWithGoogle(req, res);
			} catch (error) {
				expect(AccessValidator.validateGoogleLogin).toHaveBeenCalled();
				expect(accessService.loginWithGoogle).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleLoginWithFacebook', () => {
		const profile = { displayName: 'jest-display-name', id: 'jest-facebook-id' };

		it('should login with Facebook successfully', async () => {
			AccessValidator.validateFacebookLogin.mockReturnValue({ data: { username: profile.displayName, facebook_id: profile.id, type_login: 'facebook' }, error: false });
			accessService.loginWithFacebook.mockResolvedValue(validLoginResult);

			await AccessController.handleLoginWithFacebook(profile, res);

			expect(AccessValidator.validateFacebookLogin).toHaveBeenCalled();
			expect(accessService.loginWithFacebook).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validLoginResult),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateFacebookLogin.mockReturnValue({ data: null, error: true });
			accessService.loginWithFacebook.mockResolvedValue(validLoginResult);

			try {
				await AccessController.handleLoginWithFacebook(profile, res);
			} catch (error) {
				expect(AccessValidator.validateFacebookLogin).toHaveBeenCalled();
				expect(accessService.loginWithFacebook).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateFacebookLogin.mockReturnValue({ data: { username: profile.displayName, facebook_id: profile.id, type_login: 'facebook' }, error: false });
			accessService.loginWithFacebook.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleLoginWithFacebook(profile, res);
			} catch (error) {
				expect(AccessValidator.validateFacebookLogin).toHaveBeenCalled();
				expect(accessService.loginWithFacebook).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateFacebookLogin.mockReturnValue({ data: { username: profile.displayName, facebook_id: profile.id, type_login: 'facebook' }, error: false });
			accessService.loginWithFacebook.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleLoginWithFacebook(profile, res);
			} catch (error) {
				expect(AccessValidator.validateFacebookLogin).toHaveBeenCalled();
				expect(accessService.loginWithFacebook).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});

	describe('handleSendOTPToResetPassword', () => {
		const req = { body: { email: 'jest@tester.com' } };

		it('should send OTP to reset password successfully', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: { userEmail: req.body.email }, error: false });
			accessService.sendOTPToResetPassword.mockResolvedValue({});

			await AccessController.handleSendOTPToResetPassword(req, res);

			expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
			expect(accessService.sendOTPToResetPassword).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: { email: req.body.email },
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: null, error: true });
			accessService.sendOTPToResetPassword.mockResolvedValue({});

			try {
				await AccessController.handleSendOTPToResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
				expect(accessService.sendOTPToResetPassword).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: { userEmail: req.body.email }, error: false });
			accessService.sendOTPToResetPassword.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleSendOTPToResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
				expect(accessService.sendOTPToResetPassword).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateVerifyEmail.mockReturnValue({ data: { userEmail: req.body.email }, error: false });
			accessService.sendOTPToResetPassword.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleSendOTPToResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyEmail).toHaveBeenCalled();
				expect(accessService.sendOTPToResetPassword).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	})

	describe('handleConfirmOTPToResetPassword', () => {
		const req = { body: validVerifyOTPPayload };

		it('should confirm OTP to reset password successfully', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: { ...req.body, userEmail: req.body.email }, error: false });
			accessService.confirmOTPToResetPassword.mockResolvedValue(validVerifyOTPResult.data);

			await AccessController.handleConfirmOTPToResetPassword(req, res);

			expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
			expect(accessService.confirmOTPToResetPassword).toHaveBeenCalled();
			expect(res.status).toHaveBeenCalledWith(200);
			expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
				data: expect.objectContaining(validVerifyOTPResult.data),
			}));
		});

		it('should throw BadRequestResponse if validation failed', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: null, error: true });
			accessService.confirmOTPToResetPassword.mockResolvedValue(validVerifyOTPResult.data);

			try {
				await AccessController.handleConfirmOTPToResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
				expect(accessService.confirmOTPToResetPassword).not.toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw BadRequestResponse if a MongooseError is occurred', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: { ...req.body, userEmail: req.body.email }, error: false });
			accessService.confirmOTPToResetPassword.mockRejectedValue(new MongooseError('MongooseError'));

			try {
				await AccessController.handleConfirmOTPToResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
				expect(accessService.confirmOTPToResetPassword).toHaveBeenCalled();
				expect(error).toBeInstanceOf(BadRequestResponse);
			}
		});

		it('should throw error if an unexpected error is occurred', async () => {
			AccessValidator.validateVerifyOTP.mockReturnValue({ data: { ...req.body, userEmail: req.body.email }, error: false });
			accessService.confirmOTPToResetPassword.mockRejectedValue(new Error('Unexpected error'));

			try {
				await AccessController.handleConfirmOTPToResetPassword(req, res);
			} catch (error) {
				expect(AccessValidator.validateVerifyOTP).toHaveBeenCalled();
				expect(accessService.confirmOTPToResetPassword).toHaveBeenCalled();
				expect(error).toBeInstanceOf(Error);
			}
		});
	});
})