const ResourceService = require('../../../modules/resource/resource.service');
const { ConflictResponse, NotFoundResponse } = require('../../../response/error');
const MongooseUtil = require('../../../utils/mongoose.util');

// Mock dependencies
jest.mock('../../../utils/mongoose.util');

describe('ResourceService', () => {
  let resourceService;
  let mockResourceModel;

  // Setup mock data
  const mockResource = {
    _id: 'resource123',
    name: 'testresource',
    description: 'Test resource',
    save: jest.fn().mockImplementation(() => Promise.resolve({ _doc: mockResource }))
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
    mockResourceModel = {
      findOne: createChainableMock(),
      create: jest.fn(),
      findById: createChainableMock(),
      findByIdAndUpdate: jest.fn(),
      deleteOne: jest.fn(),
      aggregate: jest.fn(),
    };

    // Setup service with mock models
    resourceService = new ResourceService();
    resourceService.resourceModel = mockResourceModel;

    // Setup default mock implementations
    MongooseUtil.convertToMongooseObjectIdType.mockImplementation(id => id);
  });

  describe('createNewResource', () => {
    const newResourceData = {
      userId: 'user123',
      name: 'testresource',
      description: 'Test resource'
    };

    it('should create new resource successfully', async () => {
      mockResourceModel.findOne.mockResolvedValue(null);
      mockResourceModel.create.mockResolvedValue(mockResource);

      const result = await resourceService.createNewResource(newResourceData.userId, newResourceData.name, newResourceData.description);

      expect(mockResourceModel.findOne).toHaveBeenCalledWith({ name: newResourceData.name });
      expect(mockResourceModel.create).toHaveBeenCalled();
      expect(result).toEqual(mockResource);
    });

    it('should throw error if resource already exists', async () => {
      mockResourceModel.findOne.mockResolvedValue(mockResource);

      await expect(resourceService.createNewResource(newResourceData.userId, newResourceData.name, newResourceData.description))
        .rejects
        .toThrow(new ConflictResponse('Resource already exists', 1020103));
    });
  });

  describe('getResourceList', () => {
    const mockQuery = {
      limit: 10,
      page: 1,
      search: 'test',
      sort: 'name',
      sortOrder: 1
    };

    it('should get resource list successfully', async () => {
      const mockAggregateResult = [{
        results: [mockResource],
        totalCount: [{ count: 1 }]
      }];

      mockResourceModel.aggregate.mockResolvedValue(mockAggregateResult);

      const result = await resourceService.getResourceList(mockQuery);

      expect(mockResourceModel.aggregate).toHaveBeenCalled();
      expect(result).toEqual(mockAggregateResult);
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockResourceModel.aggregate.mockRejectedValue(new Error('Unexpected error'));

      await expect(resourceService.getResourceList(mockQuery))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('getResourceById', () => {
    it('should return resource by id successfully', async () => {
      mockResourceModel.findById.mockResolvedValue(mockResource);

      const result = await resourceService.getResourceById('resource123');

      expect(mockResourceModel.findById).toHaveBeenCalledWith('resource123');
      expect(result).toEqual(mockResource);
    });

    it('should throw error if resource not found', async () => {
      mockResourceModel.findById.mockResolvedValue(null);

      await expect(resourceService.getResourceById('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Resource not found', 1020303));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockResourceModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(resourceService.getResourceById('resource123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('updateResource', () => {
    const updateData = {
      slug: 'newslug',
      name: 'newname',
      description: 'New description'
    };

    it('should successfully update resource', async () => {
      mockResourceModel.findById.mockResolvedValue(mockResource);

      const result = await resourceService.updateResource('resource123', updateData);

      expect(mockResourceModel.findById).toHaveBeenCalledWith('resource123');
      expect(mockResource.save).toHaveBeenCalled();
      expect(result).toEqual(mockResource);
    });

    it('should throw error if resource not found', async () => {
      mockResourceModel.findById.mockResolvedValue(null);

      await expect(resourceService.updateResource('nonexistent', updateData))
        .rejects
        .toThrow(new NotFoundResponse('Resource not found', 1020404));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockResourceModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(resourceService.updateResource('resource123', updateData))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('deleteResource', () => {
    it('should successfully delete resource', async () => {
      mockResourceModel.findById.mockResolvedValue(mockResource);
      mockResourceModel.deleteOne.mockResolvedValue({ deletedCount: 1 });

      await resourceService.deleteResource('resource123');

      expect(mockResourceModel.findById).toHaveBeenCalledWith('resource123');
      expect(mockResourceModel.deleteOne).toHaveBeenCalledWith({ _id: 'resource123' });
    });

    it('should throw error if resource not found', async () => {
      mockResourceModel.findById.mockResolvedValue(null);

      await expect(resourceService.deleteResource('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Resource not found', 1020503));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockResourceModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(resourceService.deleteResource('resource123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });
});