const request = require('supertest');
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
const resourceRoutes = require('../../../routes/api_v1/resource.route');
const AccessMiddleware = require('../../../middlewares/access.middleware');
const permissionMiddleware = require('../../../middlewares/permission.middleware');

// Mock middleware dependencies
jest.mock('../../../middlewares/access.middleware', () => ({
  checkAccess: jest.fn((req, res, next) => next())
}));
jest.mock('../../../middlewares/permission.middleware', () => ({
  checkPermission: jest.fn(() => (req, res, next) => next())
}));

// Mock the resource controller module so that our routes return controlled responses.
jest.mock('../../../modules/resource/resource.controller', () => ({
  getResourceList: jest.fn(async (req, res) =>
    res.status(200).json({
      data: [
        { id: '1', name: 'resource1' },
        { id: '2', name: 'resource2' }
      ],
      total: 2
    })
  ),
  getResourceById: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, name: 'resource1' })
  ),
  createNewResource: jest.fn(async (req, res) => {
    // Simulate simple validation: require name.
    if (!req.body.name) {
      return res.status(400).json({ error: 'Invalid input' });
    }
    return res.status(201).json({ id: '3', ...req.body });
  }),
  updateResource: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, ...req.body })
  ),
  deleteResource: jest.fn(async (req, res) =>
    res.status(200).json({ success: true })
  ),
  getResourceOwnerIds: jest.fn(() => ['1', '2'])
}));

describe('Resource Routes', () => {
  let mockToken;

  beforeAll(() => {
    // Setup express app for testing
    app.use(express.json());
    app.use('/api/resources', resourceRoutes);

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

  describe('GET /api/resources', () => {
    it('should respond with list of resources successfully', async () => {
      const response = await request(app)
        .get('/api/resources')
        .set('Authorization', `Bearer ${mockToken}`)
        .query({ page: 1, limit: 10 });

      expect(AccessMiddleware.checkAccess).toHaveBeenCalled();
      expect(response.status).toBe(200);
      expect(response.body.data).toHaveLength(2);
    });

    it('should throw error if user is not authenticated', async () => {
      AccessMiddleware.checkAccess.mockRejectedValue(new Error('Unauthorized'));

      const response = await request(app)
        .get('/api/resources')
        .query({ page: 1, limit: 10 });

      expect(response.status).toBe(500);
    });

    it('should throw error if user lacks permission', async () => {
      permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next(new Error('Access denied')));

      const response = await request(app)
        .get('/api/resources')
        .set('Authorization', `Bearer ${mockToken}`);
      expect(response.status).toBe(500);
    });
  });

  describe('GET /api/resources/:id', () => {
    it('should return resource details when properly authenticated', async () => {
      const response = await request(app)
        .get('/api/resources/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ id: '1', name: 'resource1' });
    });
  });

  describe('POST /api/resources', () => {
    it('should create a new resource when properly authenticated', async () => {
      const newResource = {
        name: 'new-resource'
      };

      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(newResource);

      expect(response.status).toBe(201);
      expect(response.body.name).toBe(newResource.name);
    });

    it('should validate request body and return 400 for invalid input', async () => {
      const invalidResource = {
        // Missing name
      };

      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(invalidResource);

      expect(response.status).toBe(400);
    });
  });

  describe('PATCH /api/resources/:id', () => {
    it('should update resource when properly authenticated', async () => {
      const updateData = {
        name: 'updated-resource'
      };

      const response = await request(app)
        .patch('/api/resources/1')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(updateData);

      expect(response.status).toBe(200);
      expect(response.body.name).toBe(updateData.name);
    });
  });

  describe('DELETE /api/resources/:id', () => {
    it('should delete resource when properly authenticated', async () => {
      const response = await request(app)
        .delete('/api/resources/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ success: true });
    });
  });
});