const AccessService = require('../../../modules/access/access.service');
const { ConflictResponse, NotFoundResponse, BadRequestResponse, InternalServerErrorResponse } = require('../../../response/error');
const BcryptHelper = require('../../../helpers/bcrypt.helper');
const { generateRandomString, generateRSAKeysForAccess } = require('../../../utils/crypto.util');
const MongooseUtil = require('../../../utils/mongoose.util');
const JWTHelper = require('../../../helpers/jwt.helper');
const EmailHelper = require('../../../helpers/email.helper');
const GoogleHelper = require('../../../helpers/google.helper');
const jwt = require('jsonwebtoken');

const {
	mockUserResponse,
	validSignupPayload,
	mockAccessResponse,
	mockInvokeNewTokenParameters,
} = require('./access.mock');
const UserFilter = require('../../../modules/user/user.filter');

// Mock dependencies
jest.mock('../../../helpers/bcrypt.helper');
jest.mock('../../../utils/crypto.util');
jest.mock('../../../utils/mongoose.util');
jest.mock('../../../helpers/jwt.helper');
jest.mock('../../../helpers/email.helper');
jest.mock('../../../helpers/google.helper')

describe('AccessService', () => {
	let accessService;
	let mockUserModel;
	let mockRoleModel;
	let mockAccessModel;

	beforeEach(() => {
		jest.clearAllMocks();

		const createChainableMock = () => {
			const mock = jest.fn();
			mock.mockReturnValue({
				populate: jest.fn().mockReturnThis(),
				lean: jest.fn().mockReturnValue(Promise.resolve(null))
			});
			return mock;
		};

		mockUserModel = {
			findOne: createChainableMock(),
			create: jest.fn(),
			findByIdAndUpdate: jest.fn(),
			findById: createChainableMock(),
			updateOne: jest.fn(),
			deleteOne: jest.fn(),
			aggregate: jest.fn(),
		};

		mockRoleModel = {
			findOne: createChainableMock(),
		};

		mockAccessModel = {
			findById: createChainableMock(),
			create: jest.fn(),
			findOne: createChainableMock(),
			updateOne: jest.fn(),
		};

		accessService = new AccessService();
		accessService.userModel = mockUserModel;
		accessService.roleModel = mockRoleModel;
		accessService.accessModel = mockAccessModel;


		BcryptHelper.hash.mockResolvedValue('hashedPassword');
		BcryptHelper.compare.mockResolvedValue(true);
		generateRandomString.mockReturnValue('random123');
		generateRSAKeysForAccess.mockReturnValue({
			privateKey: 'privateKey',
			publicKey: 'publicKey'
		});
		MongooseUtil.convertToMongooseObjectIdType.mockImplementation(id => id);
		JWTHelper.generateAccessToken.mockReturnValue('jest-access-token');
		JWTHelper.generateRefreshToken.mockReturnValue('jest-refresh-token');
		EmailHelper.sendEmail.mockResolvedValue({});
	});

	describe('getAccessById', () => {
		it('should get access by id successfully', async () => {
			mockAccessModel.findById().lean.mockReturnValue(mockUserResponse);
			const result = await accessService.getAccessById('jest-access-id');

			expect(mockAccessModel.findById).toBeCalledWith('jest-access-id');
			expect(MongooseUtil.convertToMongooseObjectIdType).toBeCalledWith('jest-access-id');
			expect(result).toEqual(UserFilter.makeBasicFilter(mockUserResponse));
		});

		it('should throw NotFoundResponse if access is not found', async () => {
			mockAccessModel.findById().lean.mockReturnValue(null);
			try {
				await accessService.getAccessById('jest-access-id');
			} catch (error) {
				expect(mockAccessModel.findById).toBeCalledWith('jest-access-id');
				expect(MongooseUtil.convertToMongooseObjectIdType).toBeCalledWith('jest-access-id');
				expect(error).toBeInstanceOf(NotFoundResponse);
				expect(error.message).toBe('Access not found');
			}
		});

		it('should throw error if unexpected error occurs', async () => {
			mockAccessModel.findById().lean.mockRejectedValue(new Error('Unexpected error'));
			try {
				await accessService.getAccessById('jest-access-id');
			} catch (error) {
				expect(mockAccessModel.findById).toBeCalledWith('jest-access-id');
				expect(MongooseUtil.convertToMongooseObjectIdType).toBeCalledWith('jest-access-id');
				expect(error).toBeInstanceOf(Error);
				expect(error.message).toBe('Unexpected error');
			}
		});
	})

	describe('handleSignup', () => {
		it('should signup successfully', async () => {
			mockUserModel.findOne.mockResolvedValue(null);
			mockRoleModel.findOne().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.create.mockResolvedValue(mockAccessResponse);
			mockUserModel.findByIdAndUpdate.mockResolvedValue(mockUserResponse);

			const result = await accessService.handleSignup(validSignupPayload.email, validSignupPayload.password);

			expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email });
			expect(mockRoleModel.findOne).toHaveBeenCalledWith({ name: 'User' });
			expect(BcryptHelper.hash).toHaveBeenCalledWith(validSignupPayload.password);
			expect(generateRSAKeysForAccess).toHaveBeenCalled();
			expect(mockAccessModel.create).toHaveBeenCalled();
			expect(result).toEqual(UserFilter.makeBasicFilter(mockUserResponse));
		});

		it('should throw ConflictResponse if email already exists', async () => {
			mockUserModel.findOne.mockResolvedValue(mockUserResponse);

			try {
				await accessService.handleSignup(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Email already exists');
			}
		});

		it('should throw ConflictResponse if User role not found', async () => {
			mockUserModel.findOne.mockResolvedValue(null);
			mockRoleModel.findOne().lean.mockResolvedValue(null);

			try {
				await accessService.handleSignup(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email });
				expect(mockRoleModel.findOne).toHaveBeenCalledWith({ name: 'User' });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('User role not found');
			}
		});

		it('should throw error if unexpected error occurs', async () => {
			mockUserModel.findOne.mockRejectedValue(new Error('Unexpected error'));

			try {
				await accessService.handleSignup(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email });
				expect(error).toBeInstanceOf(Error);
				expect(error.message).toBe('Unexpected error');
			}
		});
	});

	describe('handleLogin', () => {
		it('should login successfully', async () => {
			mockUserModel.findOne().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			mockAccessModel.updateOne.mockResolvedValue(null);

			const result = await accessService.handleLogin(validSignupPayload.email, validSignupPayload.password);

			expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email, type_login: 'local' });
			expect(BcryptHelper.compare).toHaveBeenCalledWith(validSignupPayload.password, mockUserResponse.password);
			expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
			expect(JWTHelper.generateAccessToken).toHaveBeenCalled();
			expect(JWTHelper.generateRefreshToken).toHaveBeenCalled();
			expect(mockAccessModel.updateOne).toHaveBeenCalled();
			expect(result).toEqual({
				user: UserFilter.makeBasicFilter(mockUserResponse),
				accessToken: 'jest-access-token',
				refreshToken: 'jest-refresh-token'
			});
		});

		it('should throw ConflictResponse if user not found', async () => {
			mockUserModel.findOne().populate().lean.mockResolvedValue(null);

			try {
				await accessService.handleLogin(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email, type_login: 'local' });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Email or password is incorrect');
			}
		});

		it('should throw ConflictResponse if password is incorrect', async () => {
			mockUserModel.findOne().populate().lean.mockResolvedValue(mockUserResponse);
			BcryptHelper.compare.mockResolvedValue(false);

			try {
				await accessService.handleLogin(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email, type_login: 'local' });
				expect(BcryptHelper.compare).toHaveBeenCalledWith(validSignupPayload.password, mockUserResponse.password);
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Email or password is incorrect');
			}
		});

		it('should throw ConflictResponse if access not found', async () => {
			mockUserModel.findOne().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(null);

			try {
				await accessService.handleLogin(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email, type_login: 'local' });
				expect(BcryptHelper.compare).toHaveBeenCalledWith(validSignupPayload.password, mockUserResponse.password);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Invalid access to account');
			}
		});

		it('should throw ConflictResponse if user access does not have public key or private key', async () => {
			mockUserModel.findOne().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue({ ...mockAccessResponse, public_key: null, private_key: null });

			try {
				await accessService.handleLogin(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email, type_login: 'local' });
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Something went wrong');
			}
		});

		it('should throw error if unexpected error occurs', async () => {
			mockUserModel.findOne().populate().lean.mockRejectedValue(new Error('Unexpected error'));

			try {
				await accessService.handleLogin(validSignupPayload.email, validSignupPayload.password);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: validSignupPayload.email, type_login: 'local' });
				expect(error).toBeInstanceOf(Error);
				expect(error.message).toBe('Unexpected error');
			}
		});
	});

	describe('handleInvokeNewTokens', () => {
		const { userId, refreshToken, accessToken } = mockInvokeNewTokenParameters;

		JWTHelper.verifyToken.mockImplementation((token, key) => {
			if (token === accessToken) {
				// return { id: userId, email: mockUserResponse.email };
				throw new jwt.TokenExpiredError('Token is still valid');
			}
			return { id: userId, createdAt: new Date() };
		});

		it('should invoke new tokens successfully', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			mockAccessModel.updateOne.mockResolvedValue(null);

			const result = await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);

			expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
			expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
			expect(JWTHelper.verifyToken).toHaveBeenCalledWith(refreshToken, mockAccessResponse.public_key);
			expect(JWTHelper.verifyToken).toHaveBeenCalledWith(accessToken, mockAccessResponse.public_key);
			expect(JWTHelper.generateAccessToken).toHaveBeenCalled();
			expect(JWTHelper.generateRefreshToken).toHaveBeenCalled();
			expect(mockAccessModel.updateOne).toHaveBeenCalled();
			expect(result).toEqual({ user: UserFilter.makeBasicFilter(mockUserResponse), accessToken, refreshToken });
		});

		it('should throw ConflictResponse if user not found', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(null);

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('User not found');
			}
		});

		it('should throw ConflictResponse if access not found', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(null);

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Invalid access to account');
			}
		});

		it('should throw ConflictResponse if access public key or private key is invalid', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue({ ...mockAccessResponse, public_key: null });

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(error).toBeInstanceOf(ConflictResponse);
				expect(error.message).toBe('Something went wrong');
			}
		});

		it('should throw ConflictResponse if access token is still valid', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			JWTHelper.verifyToken.mockImplementation((token, key) => {
				if (token === accessToken) {
					return { id: userId, email: mockUserResponse.email };
				}
				return null;
			});

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(JWTHelper.verifyToken).toHaveBeenCalledWith(accessToken, mockAccessResponse.public_key);
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Invalid refresh token');
			}
		});

		it('should throw ConflictResponse if refresh token is invalid', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			JWTHelper.verifyToken.mockImplementation((token, key) => {
				if (token === accessToken) {
					throw new jwt.TokenExpiredError('Token is still valid');
				}
				return { id: userId, createdAt: new Date() };
			});

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(JWTHelper.verifyToken).toHaveBeenCalledWith(refreshToken, mockAccessResponse.public_key);
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Invalid refresh token');
			}
		});

		it('should throw ConflictResponse if decoded refresh token does not match user id', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			JWTHelper.verifyToken.mockImplementation((token, key) => {
				if (token === accessToken) {
					throw new jwt.TokenExpiredError('Token is still valid');
				}
				return { id: 'invalidUserId' };
			});

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(JWTHelper.verifyToken).toHaveBeenCalledWith(refreshToken, mockAccessResponse.public_key);
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Invalid refresh token');
			}
		});

		it('should throw ConflictResponse if refresh token has been used', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue({ ...mockAccessResponse, refresh_token_used: [{ token: refreshToken }] });
			JWTHelper.verifyToken.mockImplementation((token, key) => {
				if (token === accessToken) {
					throw new jwt.TokenExpiredError('Token is still valid');
				}
				return { id: userId };
			});

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(JWTHelper.verifyToken).toHaveBeenCalledWith(refreshToken, mockAccessResponse.public_key);
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Invalid refresh token');
			}
		});

		it('should throw ConflictResponse if unexpected error occurs in jwt', async () => {
			mockUserModel.findById().populate().lean.mockResolvedValue(mockUserResponse);
			mockAccessModel.findOne.mockResolvedValue({ ...mockAccessResponse, refresh_token_used: [{ token: refreshToken }] });
			JWTHelper.verifyToken.mockImplementation(() => {
				throw new jwt.JsonWebTokenError('Unexpected error');
			});

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: userId });
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Invalid refresh token');
			}
		});

		it('should throw error if unexpected error occurs', async () => {
			mockUserModel.findById().populate().lean.mockRejectedValue(new Error('Unexpected error'));

			try {
				await accessService.handleInvokeNewTokens(userId, accessToken, refreshToken);
			} catch (error) {
				expect(mockUserModel.findById).toHaveBeenCalledWith(userId);
				expect(error).toBeInstanceOf(Error);
				expect(error.message).toBe('Unexpected error');
			}
		});
	});

	describe('sendOTPToVerifyEmail', () => {
		it('should send OTP to verify email successfully', async () => {
			mockUserModel.findOne.mockResolvedValue({ ...mockUserResponse, email_verified: false });
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			mockAccessModel.updateOne.mockResolvedValue({ acknowledged: true, modifiedCount: 1 });

			await accessService.sendOTPToVerifyEmail(mockUserResponse.email);

			expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
			expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
			expect(EmailHelper.sendEmail).toHaveBeenCalled();
			expect(mockAccessModel.updateOne).toHaveBeenCalled();
		});

		it('should throw BadRequestResponse if user not found', async () => {
			mockUserModel.findOne.mockResolvedValue(null);

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('User not found');
			}
		});

		it('should throw BadRequestResponse if email is already verified', async () => {
			mockUserModel.findOne.mockResolvedValue(mockUserResponse);

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Email is already verified');
			}
		});

		it('should throw BadRequestResponse if access not found', async () => {
			mockUserModel.findOne.mockResolvedValue({ ...mockUserResponse, email_verified: false });
			mockAccessModel.findOne.mockResolvedValue(null);

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Invalid access to account');
			}
		});

		it('should throw BadRequestResponse if otp count is exceed 5 times in 1 hour', async () => {
			mockUserModel.findOne.mockResolvedValue({ ...mockUserResponse, email_verified: false });
			mockAccessModel.findOne.mockResolvedValue({ ...mockAccessResponse, otp_count: 5, last_otp_sent: new Date() });

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Reached the maximum number of OTP requests per hour');
			}
		});

		it('should throw BadRequestResponse if many otp codes sent without enough delay', async () => {
			mockUserModel.findOne.mockResolvedValue({ ...mockUserResponse, email_verified: false });
			mockAccessModel.findOne.mockResolvedValue({ ...mockAccessResponse, last_otp_sent: new Date() });

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
				expect(error).toBeInstanceOf(BadRequestResponse);
				expect(error.message).toBe('Please wait 30 seconds before requesting another OTP.');
			}
		});

		it('should throw InternalServerErrorResponse if unexpected error occurs in email helper', async () => {
			mockUserModel.findOne.mockResolvedValue({ ...mockUserResponse, email_verified: false });
			mockAccessModel.findOne.mockResolvedValue(mockAccessResponse);
			EmailHelper.sendEmail.mockRejectedValue(new Error('Unexpected error'));

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(mockAccessModel.findOne).toHaveBeenCalledWith({ user_id: mockUserResponse._id });
				expect(EmailHelper.sendEmail).toHaveBeenCalled();
				expect(error).toBeInstanceOf(InternalServerErrorResponse);
				expect(error.message).toBe('Failed to send OTP via email');
			}
		});

		it('should throw BadRequestResponse if unexpected error occurs', async () => {
			mockUserModel.findOne.mockRejectedValue(new Error('Unexpected error'));

			try {
				await accessService.sendOTPToVerifyEmail(mockUserResponse.email);
			} catch (error) {
				expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: mockUserResponse.email });
				expect(error).toBeInstanceOf(Error);
				expect(error.message).toBe('Unexpected error');
			}
		});
	});
});