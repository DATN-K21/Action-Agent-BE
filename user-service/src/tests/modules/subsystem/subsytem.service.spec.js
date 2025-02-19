const SubSystemService = require('../../../modules/subsystem/subsystem.service');
const { ConflictResponse } = require('../../../response/error');
const { generateRandomString } = require('../../../utils/crypto.util');

// Mock dependencies
jest.mock('../../../utils/crypto.util');

describe('SubSystemService', () => {
  let subSystemService;
  let mockSubSystemModel;

  // Setup mock data
  const mockSubSystem = {
    _id: 'subsystem123',
    name: 'testsubsystem',
    description: 'Test subsystem',
    apiKeys: 'randomApiKey',
    owners: ['owner123'],
    logo_url: 'http://example.com/logo.png',
    save: jest.fn().mockImplementation(() => Promise.resolve({ _doc: mockSubSystem }))
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
    mockSubSystemModel = {
      findOne: createChainableMock(),
      create: jest.fn(),
      findById: createChainableMock(),
      findByIdAndUpdate: jest.fn(),
      deleteOne: jest.fn(),
      find: jest.fn(),
    };

    // Setup service with mock models
    subSystemService = new SubSystemService();
    subSystemService.subSystemModel = mockSubSystemModel;

    // Setup default mock implementations
    generateRandomString.mockReturnValue('randomApiKey');
  });

  describe('getSubSystemList', () => {
    it('should return list of subsystems', async () => {
      mockSubSystemModel.find.mockResolvedValue([mockSubSystem]);

      const result = await subSystemService.getSubSystemList();

      expect(mockSubSystemModel.find).toHaveBeenCalled();
      expect(result).toEqual([mockSubSystem]);
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockSubSystemModel.find.mockRejectedValue(new Error('Unexpected error'));

      await expect(subSystemService.getSubSystemList())
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('createNewSubSystem', () => {
    const newSubSystemData = {
      name: 'testsubsystem',
      description: 'Test subsystem',
      owner: 'owner123',
      logo_url: 'http://example.com/logo.png'
    };

    it('should create new subsystem successfully', async () => {
      mockSubSystemModel.findOne.mockResolvedValue(null);
      mockSubSystemModel.create.mockResolvedValue(mockSubSystem);

      const result = await subSystemService.createNewSubSystem(newSubSystemData);

      expect(mockSubSystemModel.findOne).toHaveBeenCalledWith({ name: newSubSystemData.name });
      expect(mockSubSystemModel.create).toHaveBeenCalled();
      expect(result).toEqual(mockSubSystem);
    });

    it('should throw error if subsystem already exists', async () => {
      mockSubSystemModel.findOne.mockResolvedValue(mockSubSystem);

      await expect(subSystemService.createNewSubSystem(newSubSystemData))
        .rejects
        .toThrow(new ConflictResponse('SubSystem already exists', 1060105));
    });
  });

  describe('getSubSystemById', () => {
    it('should return subsystem by id successfully', async () => {
      mockSubSystemModel.findById.mockResolvedValue(mockSubSystem);

      const result = await subSystemService.getSubSystemById('subsystem123');

      expect(mockSubSystemModel.findById).toHaveBeenCalledWith('subsystem123');
      expect(result).toEqual(mockSubSystem);
    });

    it('should throw error if subsystem not found', async () => {
      mockSubSystemModel.findById.mockResolvedValue(null);

      await expect(subSystemService.getSubSystemById('nonexistent'))
        .rejects
        .toThrow(new ConflictResponse('SubSystem not found', 1060303));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockSubSystemModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(subSystemService.getSubSystemById('subsystem123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('updateSubSystem', () => {
    const updateData = {
      name: 'newname',
      description: 'New description',
      logo_url: 'http://example.com/newlogo.png',
      status: 'active'
    };

    it('should successfully update subsystem', async () => {
      mockSubSystemModel.findById.mockResolvedValue(mockSubSystem);

      const result = await subSystemService.updateSubSystem('subsystem123', updateData);

      expect(mockSubSystemModel.findById).toHaveBeenCalledWith('subsystem123');
      expect(mockSubSystem.save).toHaveBeenCalled();
      expect(result).toEqual(mockSubSystem);
    });

    it('should throw error if subsystem not found', async () => {
      mockSubSystemModel.findById.mockResolvedValue(null);

      await expect(subSystemService.updateSubSystem('nonexistent', updateData))
        .rejects
        .toThrow(new ConflictResponse('SubSystem not found', 1060406));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockSubSystemModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(subSystemService.updateSubSystem('subsystem123', updateData))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('deleteSubSystem', () => {
    it('should successfully delete subsystem', async () => {
      mockSubSystemModel.findById.mockResolvedValue(mockSubSystem);
      mockSubSystemModel.deleteOne.mockResolvedValue({ deletedCount: 1 });

      await subSystemService.deleteSubSystem('subsystem123');

      expect(mockSubSystemModel.findById).toHaveBeenCalledWith('subsystem123');
      expect(mockSubSystemModel.deleteOne).toHaveBeenCalledWith({ _id: 'subsystem123' });
    });

    it('should throw error if subsystem not found', async () => {
      mockSubSystemModel.findById.mockResolvedValue(null);

      await expect(subSystemService.deleteSubSystem('nonexistent'))
        .rejects
        .toThrow(new ConflictResponse('SubSystem not found', 1060503));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockSubSystemModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(subSystemService.deleteSubSystem('subsystem123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });
});