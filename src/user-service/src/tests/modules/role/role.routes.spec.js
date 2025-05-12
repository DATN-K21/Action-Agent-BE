const request = require('supertest');
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();
const roleRoutes = require('../../../routes/api_v1/role.route');
const AccessMiddleware = require('../../../middlewares/access.middleware');
const permissionMiddleware = require('../../../middlewares/permission.middleware');

// Mock middleware dependencies
jest.mock('../../../middlewares/access.middleware', () => ({
  checkAccess: jest.fn((req, res, next) => next())
}));
jest.mock('../../../middlewares/permission.middleware', () => ({
  checkPermission: jest.fn(() => (req, res, next) => next())
}));

// Mock the role controller module so that our routes return controlled responses.
jest.mock('../../../modules/role/role.controller', () => ({
  getRoleList: jest.fn(async (req, res) =>
    res.status(200).json({
      data: [
        { id: '1', name: 'role1' },
        { id: '2', name: 'role2' }
      ],
      total: 2
    })
  ),
  getRoleById: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, name: 'role1' })
  ),
  createNewRole: jest.fn(async (req, res) => {
    // Simulate simple validation: require name.
    if (!req.body.name) {
      return res.status(400).json({ error: 'Invalid input' });
    }
    return res.status(201).json({ id: '3', ...req.body });
  }),
  updateRole: jest.fn(async (req, res) =>
    res.status(200).json({ id: req.params.id, ...req.body })
  ),
  deleteRole: jest.fn(async (req, res) =>
    res.status(200).json({ success: true })
  )
}));

describe('Role Routes', () => {
  let mockToken;

  beforeAll(() => {
    // Setup express app for testing
    app.use(express.json());
    app.use('/api/roles', roleRoutes);

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

  describe('GET /api/roles', () => {
    it('should respond with list of roles successfully', async () => {
      const response = await request(app)
        .get('/api/roles')
        .set('Authorization', `Bearer ${mockToken}`)
        .query({ page: 1, limit: 10 });

      expect(AccessMiddleware.checkAccess).toHaveBeenCalled();
      expect(response.status).toBe(200);
      expect(response.body.data).toHaveLength(2);
    });

    it('should throw error if user is not authenticated', async () => {
      AccessMiddleware.checkAccess.mockRejectedValue(new Error('Unauthorized'));

      const response = await request(app)
        .get('/api/roles')
        .query({ page: 1, limit: 10 });

      expect(response.status).toBe(500);
    });

    it('should throw error if user lacks permission', async () => {
      permissionMiddleware.checkPermission.mockImplementation(() => (req, res, next) => next(new Error('Access denied')));

      const response = await request(app)
        .get('/api/roles')
        .set('Authorization', `Bearer ${mockToken}`);
      expect(response.status).toBe(500);
    });
  });

  describe('GET /api/roles/:id', () => {
    it('should return role details when properly authenticated', async () => {
      const response = await request(app)
        .get('/api/roles/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ id: '1', name: 'role1' });
    });
  });

  describe('POST /api/roles', () => {
    it('should create a new role when properly authenticated', async () => {
      const newRole = {
        name: 'new-role'
      };

      const response = await request(app)
        .post('/api/roles')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(newRole);

      expect(response.status).toBe(201);
      expect(response.body.name).toBe(newRole.name);
    });

    it('should validate request body and return 400 for invalid input', async () => {
      const invalidRole = {
        // Missing name
      };

      const response = await request(app)
        .post('/api/roles')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(invalidRole);

      expect(response.status).toBe(400);
    });
  });

  describe('PATCH /api/roles/:id', () => {
    it('should update role when properly authenticated', async () => {
      const updateData = {
        name: 'updated-role'
      };

      const response = await request(app)
        .patch('/api/roles/1')
        .set('Authorization', `Bearer ${mockToken}`)
        .send(updateData);

      expect(response.status).toBe(200);
      expect(response.body.name).toBe(updateData.name);
    });
  });

  describe('DELETE /api/roles/:id', () => {
    it('should delete role when properly authenticated', async () => {
      const response = await request(app)
        .delete('/api/roles/1')
        .set('Authorization', `Bearer ${mockToken}`);

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ success: true });
    });
  });
});