const RoleService = require('../../../modules/role/role.service');
const { ConflictResponse, NotFoundResponse } = require('../../../response/error');
const MongooseUtil = require('../../../utils/mongoose.util');

// Mock dependencies
jest.mock('../../../utils/mongoose.util');

describe('RoleService', () => {
  let roleService;
  let mockRoleModel;

  // Setup mock data
  const mockRole = {
    _id: 'role123',
    name: 'testrole',
    description: 'Test role',
    grants: [],
    save: jest.fn().mockImplementation(() => Promise.resolve({ _doc: mockRole }))
  };

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    const createChainableMock = () => {
      const mock = jest.fn();
      mock.mockReturnValue({
        populate: jest.fn().mockReturnThis(),
        lean: jest.fn().mockReturnValue(Promise.resolve(null))
      });
      return mock;
    };

    // Create mock models
    mockRoleModel = {
      findOne: createChainableMock(),
      create: jest.fn(),
      findById: createChainableMock(),
      findByIdAndUpdate: jest.fn(),
      deleteOne: jest.fn(),
      aggregate: jest.fn(),
    };

    // Setup service with mock models
    roleService = new RoleService();
    roleService.roleModel = mockRoleModel;

    // Setup default mock implementations
    MongooseUtil.convertToMongooseObjectIdType.mockImplementation(id => id);
  });

  describe('createNewRole', () => {
    const newRoleData = {
      userId: 'user123',
      name: 'testrole',
      description: 'Test role',
      grants: []
    };

    it('should create new role successfully', async () => {
      mockRoleModel.findOne.mockResolvedValue(null);
      mockRoleModel.create.mockResolvedValue(mockRole);

      const result = await roleService.createNewRole(newRoleData.userId, newRoleData.name, newRoleData.description, newRoleData.grants);

      expect(mockRoleModel.findOne).toHaveBeenCalledWith({ name: newRoleData.name });
      expect(mockRoleModel.create).toHaveBeenCalled();
      expect(result).toEqual(mockRole);
    });

    it('should throw error if role already exists', async () => {
      mockRoleModel.findOne.mockResolvedValue(mockRole);

      await expect(roleService.createNewRole(newRoleData.userId, newRoleData.name, newRoleData.description, newRoleData.grants))
        .rejects
        .toThrow(new ConflictResponse('Role already exists', 1030105));
    });
  });

  describe('getRoleList', () => {
    const mockQuery = {
      limit: 10,
      page: 1,
      search: 'test',
      sort: 'name',
      sortOrder: 1
    };

    it('should get role list successfully', async () => {
      const mockAggregateResult = [{
        results: [mockRole],
        totalCount: [{ count: 1 }]
      }];

      mockRoleModel.aggregate.mockResolvedValue(mockAggregateResult);

      const result = await roleService.getRoleList(mockQuery);

      expect(mockRoleModel.aggregate).toHaveBeenCalled();
      expect(result).toEqual({
        data: mockAggregateResult[0].results,
        total: mockAggregateResult[0].totalCount[0] ? mockAggregateResult[0].totalCount[0].count : 0,
      });
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.aggregate.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.getRoleList(mockQuery))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('getRoleById', () => {
    it('should return role by id successfully', async () => {
      mockRoleModel.findById.mockResolvedValue(mockRole);

      const result = await roleService.getRoleById('role123');

      expect(mockRoleModel.findById).toHaveBeenCalledWith('role123');
      expect(result).toEqual(mockRole);
    });

    it('should throw error if role not found', async () => {
      mockRoleModel.findById.mockResolvedValue(null);

      await expect(roleService.getRoleById('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Role not found', 1030303));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.getRoleById('role123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('getRoleByName', () => {
    it('should return role by name successfully', async () => {
      mockRoleModel.findOne().lean.mockResolvedValue(mockRole);

      const result = await roleService.getRoleByName('testrole');

      expect(mockRoleModel.findOne).toHaveBeenCalledWith({ name: 'testrole' });
      expect(result).toEqual(mockRole);
    });

    it('should throw error if role not found', async () => {
      mockRoleModel.findOne().lean.mockResolvedValue(null);

      await expect(roleService.getRoleByName('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Role not found', 1030303));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.findOne().lean.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.getRoleByName('testrole'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('updateRole', () => {
    const updateData = {
      slug: 'newslug',
      name: 'newname',
      description: 'New description',
      grants: []
    };

    it('should successfully update role', async () => {
      mockRoleModel.findById.mockResolvedValue(mockRole);

      const result = await roleService.updateRole('role123', updateData);

      expect(mockRoleModel.findById).toHaveBeenCalledWith('role123');
      expect(mockRole.save).toHaveBeenCalled();
      expect(result).toEqual(mockRole);
    });

    it('should throw error if role not found', async () => {
      mockRoleModel.findById.mockResolvedValue(null);

      await expect(roleService.updateRole('nonexistent', updateData))
        .rejects
        .toThrow(new NotFoundResponse('Role not found', 1030404));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.updateRole('role123', updateData))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('deleteRole', () => {
    it('should successfully delete role', async () => {
      mockRoleModel.findById.mockResolvedValue(mockRole);
      mockRoleModel.deleteOne.mockResolvedValue({ deletedCount: 1 });

      await roleService.deleteRole('role123');

      expect(mockRoleModel.findById).toHaveBeenCalledWith('role123');
      expect(mockRoleModel.deleteOne).toHaveBeenCalledWith({ _id: 'role123' });
    });

    it('should throw error if role not found', async () => {
      mockRoleModel.findById.mockResolvedValue(null);

      await expect(roleService.deleteRole('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Role not found', 1030503));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.deleteRole('role123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('getPermissionGrantList', () => {
    const mockQuery = {
      limit: 10,
      page: 1,
      search: 'test',
      sort: 'role',
      sortOrder: 1
    };

    it('should get permission grant list successfully', async () => {
      const mockAggregateResult = [{
        results: [mockRole],
        totalCount: [{ count: 1 }]
      }];

      mockRoleModel.aggregate.mockResolvedValue(mockAggregateResult);

      const result = await roleService.getPermissionGrantList(mockQuery);

      expect(mockRoleModel.aggregate).toHaveBeenCalled();
      expect(result).toEqual({
        data: mockAggregateResult[0].results,
        total: mockAggregateResult[0].totalCount[0] ? mockAggregateResult[0].totalCount[0].count : 0,
      });
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.aggregate.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.getPermissionGrantList(mockQuery))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('addNewGrantsToRole', () => {
    const newGrant = {
      resource: 'resource123',
      actions: ['read', 'write'],
      attributes: ['*']
    };

    it('should successfully add new grants to role', async () => {
      mockRoleModel.findById.mockResolvedValue(mockRole);

      const result = await roleService.addNewGrantsToRole('role123', newGrant);

      expect(mockRoleModel.findById).toHaveBeenCalledWith('role123');
      expect(mockRole.save).toHaveBeenCalled();
      expect(result).toEqual(mockRole);
    });

    it('should throw error if role not found', async () => {
      mockRoleModel.findById.mockResolvedValue(null);

      await expect(roleService.addNewGrantsToRole('nonexistent', newGrant))
        .rejects
        .toThrow(new NotFoundResponse('Role not found', 1030705));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.addNewGrantsToRole('role123', newGrant))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('getGrantsByRole', () => {
    it('should return grants by role successfully', async () => {
      mockRoleModel.findById().populate().lean.mockResolvedValue(mockRole);

      const result = await roleService.getGrantsByRole('role123');

      expect(mockRoleModel.findById).toHaveBeenCalledWith('role123');
      expect(result).toEqual(mockRole.grants);
    });

    it('should throw error if role not found', async () => {
      mockRoleModel.findById().populate().lean.mockResolvedValue(null);

      await expect(roleService.getGrantsByRole('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Role not found', 1030805));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockRoleModel.findById().populate().lean.mockRejectedValue(new Error('Unexpected error'));

      await expect(roleService.getGrantsByRole('role123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });
});