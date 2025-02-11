const request = require('supertest');
const express = require('express');
const app = express();
const jwt = require('jsonwebtoken');
const accessRoutes = require('../../../routes/api_v1/access.route');
const AccessMiddleware = require('../../../middlewares/access.middleware');
const permissionMiddleware = require('../../../middlewares/permission.middleware');
const {
	validSignupPayload,
} = require('./access.mock');


jest.mock('../../../middlewares/access.middleware', () => ({
	checkAccess: jest.fn((req, res, next) => next())
}));
jest.mock('../../../middlewares/permission.middleware', () => ({
	checkPermission: jest.fn(() => (req, res, next) => next())
}));

jest.mock('passport', () => ({
	authenticate: jest.fn(() => (req, res, next) => {
		if (req.path === '/facebook/auth') {
			return res.status(200).json({ data: {} });
		}

		return next();
	})
}));
jest.mock('../../../modules/access/access.controller', () => ({
	handleSignup: jest.fn(async (req, res) => {
		return res.status(201).json({
			data: { email: req.body.email, password: req.body.password },
		})
	}),
	handleLogin: jest.fn(async (req, res) => {
		return res.status(200).json({
			data: {
				user: { email: req.body.email, password: req.body.password },
				accessToken: 'access-token',
				refreshToken: 'refresh-token',
			}
		});
	}),
	handleInvokeNewTokens: jest.fn(async (req, res) => {
		return res.status(200).json({
			data: {
				user: { id: req.headers['x-client-id'] },
				refreshToken: req.body.refreshToken,
				accessToken: req.headers['authorization'].split(' ')[1],
			}
		});
	}),
	handleVerifyEmail: jest.fn(async (req, res) => {
		return res.status(200).json({
			data: {
				email: req.body.email,
			}
		});
	}),
	handleVerifyOTP: jest.fn(async (req, res) => {
		return res.status(200).json({ data: { email: 'jest@tester.com' } });
	}),
	handleLogout: jest.fn(async (req, res) => {
		if (!req.headers.authorization || !req.headers['x-client-id']) {
			return res.status(401).json({ error: 'Authentication credential is required' });
		}
		return res.status(200).json({});
	}),
	handleSendOTPToResetPassword: jest.fn(async (req, res) => {
		return res.status(200).json({ data: { email: req.body.email } });
	}),
	handleConfirmOTPToResetPassword: jest.fn(async (req, res) => {
		return res.status(200).json({ data: { email: req.body.email } });
	}),
	handleResetPassword: jest.fn(async (req, res) => {
		if (!req.headers.authorization || !req.headers['x-client-id']) {
			return res.status(401).json({ error: 'Authentication credential is required' });
		}
		return res.status(200).json({
			data: { email: req.body.email },
		});
	}),
	handleLoginWithGoogle: jest.fn(async (req, res) => {
		return res.status(200).json({
			data: {
				user: { id: req.body.id_token },
				accessToken: 'access-token',
				refreshToken: 'refresh-token',
			}
		});
	}),
	handleLoginWithFacebook: jest.fn(async (req, res) => {
		return res.status(200).json({ data: {} });
	}),
}));

describe('Access Routes', () => {
	let mockToken;

	beforeAll(() => {
		// Setup express app for testing
		app.use(express.json());
		app.use('/api/access', accessRoutes);

		app.use((err, req, res, next) => {
			res.status(500).json({ error: err.message });
		});

		// Create a mock JWT token
		mockToken = jwt.sign({ userId: 'test-user123' }, 'your-secret-key');
	});

	beforeEach(() => {
		// Reset all mocks
		jest.clearAllMocks();

		// Setup default middleware behavior: simply call next()
		AccessMiddleware.checkAccess.mockImplementation((req, res, next) => next());
		permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next());
	});

	describe('POST /signup', () => {
		it('should sign up successfully', async () => {
			const response = await request(app)
				.post('/api/access/signup')
				.send(validSignupPayload);

			expect(response.statusCode).toBe(201);
			expect(response.body.data).toEqual(validSignupPayload);
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleSignup').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/signup')
				.send(validSignupPayload);

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		})
	});

	describe('POST /login', () => {
		it('should login successfully', async () => {
			const response = await request(app)
				.post('/api/access/login')
				.send({ email: 'jest@tester.com', password: '123456' });

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({
				user: { email: 'jest@tester.com', password: '123456' },
				accessToken: expect.any(String),
				refreshToken: expect.any(String),
			});
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleLogin').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/login')
				.send({ email: 'jest@tester.com', password: '123456' });

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('POST /verify/send-otp', () => {
		it('should verify email successfully', async () => {
			const response = await request(app)
				.post('/api/access/verify/send-otp')
				.send({ email: 'jest@tester.com' });

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({ email: 'jest@tester.com' });
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleVerifyEmail').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/verify/send-otp')
				.send({ email: 'jest@tester.com' });

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('POST /verify/confirm-otp', () => {
		it('should verify OTP successfully', async () => {
			const response = await request(app)
				.post('/api/access/verify/confirm-otp')
				.send({ email: 'jest@tester.com', otp: '123456' });

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({ email: 'jest@tester.com' });
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleVerifyOTP').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/verify/confirm-otp')
				.send({ email: 'jest@tester.com', otp: '123456' });

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('POST /google/auth', () => {
		it('should authenticate with Google successfully', async () => {
			const response = await request(app)
				.post('/api/access/google/auth')
				.send({ id_token: 'jest-id-token' });

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({
				user: { id: 'jest-id-token' },
				accessToken: expect.any(String),
				refreshToken: expect.any(String),
			});
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleLoginWithGoogle').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/google/auth')
				.send({ id_token: 'jest-id-token' });

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('GET /facebook/auth', () => {
		it('should authenticate with Facebook successfully', async () => {
			const response = await request(app)
				.get('/api/access/facebook/auth')

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({});
		});
	});

	describe('GET /facebook/verify', () => {
		it('should verify Facebook login successfully', async () => {
			const response = await request(app)
				.get('/api/access/facebook/verify')

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({});
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleLoginWithFacebook').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.get('/api/access/facebook/verify')

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('POST /invoke-new-tokens', () => {
		it('should invoke new tokens successfully', async () => {
			const response = await request(app)
				.post('/api/access/invoke-new-tokens')
				.set('x-client-id', 'jest-client-id')
				.set('authorization', 'Bearer jest-access-token')
				.send({ refreshToken: 'jest-refresh-token' });

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({
				user: { id: 'jest-client-id' },
				refreshToken: 'jest-refresh-token',
				accessToken: 'jest-access-token',
			});
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleInvokeNewTokens').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/invoke-new-tokens')
				.set('x-client-id', 'jest-client-id')
				.set('authorization', 'Bearer jest-access-token')
				.send({ refreshToken: 'jest-refresh-token' });

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('POST /reset-password', () => {
		it('should reset password successfully', async () => {
			const response = await request(app)
				.post('/api/access/reset-password')
				.set('x-client-id', 'jest-client-id')
				.set('authorization', 'Bearer jest-access-token')
				.send({ email: 'jest@tester.com', newPassword: '123456', confirmNewPassword: '123456' });

			expect(response.statusCode).toBe(200);
			expect(response.body.data).toEqual({ email: 'jest@tester.com' });
		});

		it('should throw an error if no token is provided', async () => {
			const response = await request(app)
				.post('/api/access/reset-password')
				.send({ email: 'jest@tester.com', newPassword: '123456', confirmNewPassword: '123456' });

			expect(response.status).toBe(401);
			expect(response.body.error).toBe('Authentication credential is required');
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleResetPassword').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/reset-password')
				.set('x-client-id', 'jest-client-id')
				.set('authorization', 'Bearer jest-access-token')
				.send({ email: 'jest@tester.com', newPassword: '123456', confirmNewPassword: '123456' });

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});

	describe('POST /logout', () => {
		it('should logout successfully', async () => {
			const response = await request(app)
				.post('/api/access/logout')
				.set('x-client-id', 'jest-client-id')
				.set('authorization', `Bearer ${mockToken}`);

			expect(response.statusCode).toBe(200);
			expect(response.body).toEqual({});
		});

		it('should throw an error if no token is provided', async () => {
			const response = await request(app)
				.post('/api/access/logout');

			expect(response.status).toBe(401);
			expect(response.body.error).toBe('Authentication credential is required');
		});

		it('should throw an error if another error occurred in access controller', async () => {
			const errorMessage = 'An error occurred';
			jest.spyOn(require('../../../modules/access/access.controller'), 'handleLogout').mockImplementation(() => {
				throw new Error(errorMessage);
			});

			const response = await request(app)
				.post('/api/access/logout')
				.set('authorization', `Bearer ${mockToken}`);

			expect(response.status).toBe(500);
			expect(response.body.error).toBe(errorMessage);
		});
	});
});