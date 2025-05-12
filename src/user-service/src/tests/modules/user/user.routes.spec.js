const request = require('supertest');
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
const userRoutes = require('../../../routes/api_v1/user.route');
const AccessMiddleware = require('../../../middlewares/access.middleware');
const permissionMiddleware = require('../../../middlewares/permission.middleware');

// Mock middleware dependencies
jest.mock('../../../middlewares/access.middleware', () => ({
	checkAccess: jest.fn((req, res, next) => next())
}));
jest.mock('../../../middlewares/permission.middleware', () => ({
	checkPermission: jest.fn(() => (req, res, next) => next())
}));

// Mock the user controller module so that our routes return controlled responses.
jest.mock('../../../modules/user/user.controller', () => ({
	getUserList: jest.fn(async (req, res) =>
		res.status(200).json({
			data: [
				{ id: '1', username: 'user1' },
				{ id: '2', username: 'user2' }
			],
			total: 2
		})
	),
	getUserById: jest.fn(async (req, res) =>
		res.status(200).json({ id: req.params.id, username: 'user1' })
	),
	createNewUser: jest.fn(async (req, res) => {
		// Simulate simple validation: require email and password.
		if (!req.body.email || !req.body.password) {
			return res.status(400).json({ error: 'Invalid input' });
		}
		return res.status(201).json({ id: '3', ...req.body });
	}),
	updateUser: jest.fn(async (req, res) =>
		res.status(200).json({ id: req.params.id, ...req.body })
	),
	deleteUser: jest.fn(async (req, res) =>
		res.status(200).json({ success: true })
	)
}));

describe('User Routes', () => {
	let mockToken;

	beforeAll(() => {
		// Setup express app for testing
		app.use(express.json());
		app.use('/api/users', userRoutes);

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

	describe('GET /api/users', () => {
		it('should respond with list of users successfully', async () => {
			const response = await request(app)
				.get('/api/users')
				.set('Authorization', `Bearer ${mockToken}`)
				.query({ page: 1, limit: 10 });

			expect(AccessMiddleware.checkAccess).toHaveBeenCalled();
			expect(response.status).toBe(200);
			expect(response.body.data).toHaveLength(2);
		});

		it('should throw error if user is not authenticated', async () => {
			AccessMiddleware.checkAccess.mockRejectedValue(new Error('Unauthorized'));

			const response = await request(app)
				.get('/api/users')
				.query({ page: 1, limit: 10 });

			expect(response.status).toBe(500);
		});

		it('should throw error if user lacks permission', async () => {
			permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next(new Error('Access denied')));

			const response = await request(app)
				.get('/api/users')
				.set('Authorization', `Bearer ${mockToken}`);
			expect(response.status).toBe(500);
		});
	});

	describe('GET /api/users/:id', () => {
		it('should return user details when properly authenticated', async () => {
			const response = await request(app)
				.get('/api/users/1')
				.set('Authorization', `Bearer ${mockToken}`);

			expect(response.status).toBe(200);
			expect(response.body).toEqual({ id: '1', username: 'user1' });
		});
	});

	describe('POST /api/users', () => {
		it('should create a new user when properly authenticated', async () => {
			const newUser = {
				username: 'new-user',
				email: 'new@example.com',
				password: 'password123'
			};

			const response = await request(app)
				.post('/api/users')
				.set('Authorization', `Bearer ${mockToken}`)
				.send(newUser);

			expect(response.status).toBe(201);
			expect(response.body.username).toBe(newUser.username);
		});

		it('should validate request body and return 400 for invalid input', async () => {
			const invalidUser = {
				username: 'new-user'
				// Missing email and password
			};

			const response = await request(app)
				.post('/api/users')
				.set('Authorization', `Bearer ${mockToken}`)
				.send(invalidUser);

			expect(response.status).toBe(400);
		});
	});

	describe('PATCH /api/users/:id', () => {
		it('should update user when properly authenticated', async () => {
			const updateData = {
				username: 'updated-user'
			};

			const response = await request(app)
				.patch('/api/users/1')
				.set('Authorization', `Bearer ${mockToken}`)
				.send(updateData);

			expect(response.status).toBe(200);
			expect(response.body.username).toBe(updateData.username);
		});
	});

	describe('DELETE /api/users/:id', () => {
		it('should delete user when properly authenticated', async () => {
			const response = await request(app)
				.delete('/api/users/1')
				.set('Authorization', `Bearer ${mockToken}`);

			expect(response.status).toBe(200);
			expect(response.body).toEqual({ success: true });
		});
	});
});
