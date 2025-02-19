const request = require('supertest');
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
const profileRoutes = require('../../../routes/api_v1/profile.route');
const AccessMiddleware = require('../../../middlewares/access.middleware');
const permissionMiddleware = require('../../../middlewares/permission.middleware');

// Mock middleware dependencies
jest.mock('../../../middlewares/access.middleware', () => ({
	checkAccess: jest.fn((req, res, next) => next())
}));
jest.mock('../../../middlewares/permission.middleware', () => ({
	checkPermission: jest.fn(() => (req, res, next) => next())
}));

// Mock the profile controller module so that our routes return controlled responses.
jest.mock('../../../modules/profile/profile.controller', () => ({
	getProfileList: jest.fn(async (req, res) =>
		res.status(200).json({
			data: [
				{ id: '1', username: 'profile1' },
				{ id: '2', username: 'profile2' }
			],
			total: 2
		})
	),
	getProfileById: jest.fn(async (req, res) =>
		res.status(200).json({ id: req.params.id, username: 'profile1' })
	),
	createNewProfile: jest.fn(async (req, res) => {
		// Simulate simple validation: require email and password.
		if (!req.body.email || !req.body.password) {
			return res.status(400).json({ error: 'Invalid input' });
		}
		return res.status(201).json({ id: '3', ...req.body });
	}),
	updateProfile: jest.fn(async (req, res) =>
		res.status(200).json({ id: req.params.id, ...req.body })
	),
	deleteProfile: jest.fn(async (req, res) =>
		res.status(200).json({ success: true })
	)
}));

describe('Profile Routes', () => {
	let mockToken;

	beforeAll(() => {
		// Setup express app for testing
		app.use(express.json());
		app.use('/api/profiles', profileRoutes);

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

	describe('GET /api/profiles', () => {
		it('should respond with list of profiles successfully', async () => {
			const response = await request(app)
				.get('/api/profiles')
				.set('Authorization', `Bearer ${mockToken}`)
				.query({ page: 1, limit: 10 });

			expect(AccessMiddleware.checkAccess).toHaveBeenCalled();
			expect(response.status).toBe(200);
			expect(response.body.data).toHaveLength(2);
		});

		it('should throw error if user is not authenticated', async () => {
			AccessMiddleware.checkAccess.mockRejectedValue(new Error('Unauthorized'));

			const response = await request(app)
				.get('/api/profiles')
				.query({ page: 1, limit: 10 });

			expect(response.status).toBe(500);
		});

		it('should throw error if user lacks permission', async () => {
			permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next(new Error('Access denied')));

			const response = await request(app)
				.get('/api/profiles')
				.set('Authorization', `Bearer ${mockToken}`);
			expect(response.status).toBe(500);
		});
	});

	describe('GET /api/profiles/:id', () => {
		it('should return profile details when properly authenticated', async () => {
			const response = await request(app)
				.get('/api/profiles/1')
				.set('Authorization', `Bearer ${mockToken}`);

			expect(response.status).toBe(200);
			expect(response.body).toEqual({ id: '1', username: 'profile1' });
		});
	});

	describe('POST /api/profiles', () => {
		it('should create a new profile when properly authenticated', async () => {
			const newProfile = {
				username: 'new-profile',
				email: 'new@example.com',
				password: 'password123'
			};

			const response = await request(app)
				.post('/api/profiles')
				.set('Authorization', `Bearer ${mockToken}`)
				.send(newProfile);

			expect(response.status).toBe(201);
			expect(response.body.username).toBe(newProfile.username);
		});

		it('should validate request body and return 400 for invalid input', async () => {
			const invalidProfile = {
				username: 'new-profile'
				// Missing email and password
			};

			const response = await request(app)
				.post('/api/profiles')
				.set('Authorization', `Bearer ${mockToken}`)
				.send(invalidProfile);

			expect(response.status).toBe(400);
		});
	});

	describe('PATCH /api/profiles/:id', () => {
		it('should update profile when properly authenticated', async () => {
			const updateData = {
				username: 'updated-profile'
			};

			const response = await request(app)
				.patch('/api/profiles/1')
				.set('Authorization', `Bearer ${mockToken}`)
				.send(updateData);

			expect(response.status).toBe(200);
			expect(response.body.username).toBe(updateData.username);
		});
	});

	describe('DELETE /api/profiles/:id', () => {
		it('should delete profile when properly authenticated', async () => {
			const response = await request(app)
				.delete('/api/profiles/1')
				.set('Authorization', `Bearer ${mockToken}`);

			expect(response.status).toBe(200);
			expect(response.body).toEqual({ success: true });
		});
	});
});