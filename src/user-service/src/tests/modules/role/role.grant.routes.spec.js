const request = require('supertest');
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
const roleGrantRoutes = require('../../../routes/api_v1/role.grant.route');
const permissionMiddleware = require('../../../middlewares/permission.middleware');

// Mock middleware dependencies
jest.mock('../../../middlewares/permission.middleware', () => ({
  checkPermission: jest.fn(() => (req, res, next) => next())
}));

// Mock the role controller module so that our routes return controlled responses.
jest.mock('../../../modules/role/role.controller', () => ({
  getPermissionGrantList: jest.fn(async (req, res) =>
    res.status(200).json({
      data: [
        { id: '1', permission: 'read' },
        { id: '2', permission: 'write' }
      ],
      total: 2
    })
  ),
  getGrantsByRole: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, permissions: ['read', 'write'] })
  ),
  addNewGrantsToRole: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, permissions: req.body.permissions })
  ),
  getRoleOwnerIds: jest.fn(() => ['1', '2'])
}));

describe('Role Grant Routes', () => {
  let mockToken;

  beforeAll(() => {
    // Setup express app for testing
    app.use(express.json());
    app.use('/api/roles/grant', roleGrantRoutes);

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
    permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next());
  });

  describe('GET /api/roles/grant', () => {
    it('should respond with list of permission grants successfully', async () => {
      const response = await request(app)
        .get('/api/roles/grant')
        .set('Authorization', `Bearer ${mockToken}`)
        .query({ page: 1, limit: 10 });

      expect(permissionMiddleware.checkPermission).toHaveBeenCalled();
      expect(response.status).toBe(200);
      expect(response.body.data).toHaveLength(2);
    });

    it('should throw error if user lacks permission', async () => {
      permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next(new Error('Access denied')));

      const response = await request(app)
        .get('/api/roles/grant')
        .set('Authorization', `Bearer ${mockToken}`);
      expect(response.status).toBe(500);
    });
  });

  describe('GET /api/roles/grant/:id', () => {
    it('should return grants by role when properly authenticated', async () => {
      const response = await request(app)
        .get('/api/roles/grant/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ id: '1', permissions: ['read', 'write'] });
    });
  });

  describe('PATCH /api/roles/grant/:id', () => {
    it('should add new grants to role when properly authenticated', async () => {
      const newGrants = {
        permissions: ['execute']
      };

      const response = await request(app)
        .patch('/api/roles/grant/1')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(newGrants);

      expect(response.status).toBe(200);
      expect(response.body.permissions).toEqual(newGrants.permissions);
    });
  });
});