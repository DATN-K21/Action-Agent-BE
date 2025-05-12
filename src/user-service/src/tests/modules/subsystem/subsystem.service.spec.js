const request = require('supertest');
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
const subSystemRoutes = require('../../../routes/api_v1/subsystem.route');
const AccessMiddleware = require('../../../middlewares/access.middleware');
const permissionMiddleware = require('../../../middlewares/permission.middleware');
const subSystemController = require('../../../modules/subsystem/subsystem.controller');

// Mock middleware dependencies
jest.mock('../../../middlewares/access.middleware', () => ({
  checkAccess: jest.fn((req, res, next) => next())
}));
jest.mock('../../../middlewares/permission.middleware', () => ({
  checkPermission: jest.fn(() => (req, res, next) => next())
}));

// Mock the subsystem controller module so that our routes return controlled responses.
jest.mock('../../../modules/subsystem/subsystem.controller', () => ({
  getSubSystemList: jest.fn(async (req, res) =>
    res.status(200).json({
      data: [
        { id: '1', name: 'subsystem1' },
        { id: '2', name: 'subsystem2' }
      ],
      total: 2
    })
  ),
  getSubSystemById: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, name: 'subsystem1' })
  ),
  createNewSubSystem: jest.fn(async (req, res) => {
    // Simulate simple validation: require name.
    if (!req.body.name) {
      return res.status(400).json({ error: 'Invalid input' });
    }
    return res.status(201).json({ id: '3', ...req.body });
  }),
  updateSubSystem: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, ...req.body })
  ),
  deleteSubSystem: jest.fn(async (req, res) =>
    res.status(200).json({ success: true })
  )
}));

describe('SubSystem Routes', () => {
  let mockToken;

  beforeAll(() => {
    // Setup express app for testing
    app.use(express.json());
    app.use('/api/subsystems', subSystemRoutes);

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

  describe('GET /api/subsystems', () => {
    it('should respond with list of subsystems successfully', async () => {
      const response = await request(app)
        .get('/api/subsystems')
        .set('Authorization', `Bearer ${mockToken}`)
        .query({ page: 1, limit: 10 });

      expect(AccessMiddleware.checkAccess).toHaveBeenCalled();
      expect(response.status).toBe(200);
      expect(response.body.data).toHaveLength(2);
    });

    it('should throw error if user is not authenticated', async () => {
      AccessMiddleware.checkAccess.mockRejectedValue(new Error('Unauthorized'));

      const response = await request(app)
        .get('/api/subsystems')
        .query({ page: 1, limit: 10 });

      expect(response.status).toBe(500);
    });

    it('should throw error if user lacks permission', async () => {
      permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next(new Error('Access denied')));

      const response = await request(app)
        .get('/api/subsystems')
        .set('Authorization', `Bearer ${mockToken}`);
      expect(response.status).toBe(500);
    });
  });

  describe('GET /api/subsystems/:id', () => {
    it('should return subsystem details when properly authenticated', async () => {
      const response = await request(app)
        .get('/api/subsystems/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ id: '1', name: 'subsystem1' });
    });
  });

  describe('POST /api/subsystems', () => {
    it('should create a new subsystem when properly authenticated', async () => {
      const newSubSystem = {
        name: 'new-subsystem',
        description: 'New subsystem description',
        owner: 'owner123',
        logo_url: 'http://example.com/logo.png'
      };

      const response = await request(app)
        .post('/api/subsystems')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(newSubSystem);

      expect(response.status).toBe(201);
      expect(response.body.name).toBe(newSubSystem.name);
    });

    it('should validate request body and return 400 for invalid input', async () => {
      const invalidSubSystem = {
        // Missing name
      };

      const response = await request(app)
        .post('/api/subsystems')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(invalidSubSystem);

      expect(response.status).toBe(400);
    });
  });

  describe('PATCH /api/subsystems/:id', () => {
    it('should update subsystem when properly authenticated', async () => {
      const updateData = {
        name: 'updated-subsystem',
        description: 'Updated description'
      };

      const response = await request(app)
        .patch('/api/subsystems/1')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(updateData);

      expect(response.status).toBe(200);
      expect(response.body.name).toBe(updateData.name);
    });
  });

  describe('DELETE /api/subsystems/:id', () => {
    it('should delete subsystem when properly authenticated', async () => {
      const response = await request(app)
        .delete('/api/subsystems/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ success: true });
    });
  });
});