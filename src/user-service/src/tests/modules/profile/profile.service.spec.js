const ProfileService = require('../../../modules/profile/profile.service');
const { NotFoundResponse, ConflictResponse } = require('../../../response/error');
const MongooseUtil = require('../../../utils/mongoose.util');
const UserService = require('../../../modules/user/user.service');
const ProfileFilter = require('../../../modules/profile/profile.filter');
const UserFilter = require('../../../modules/user/user.filter');

// Mock dependencies
jest.mock('../../../modules/user/user.service');
jest.mock('../../../utils/mongoose.util');

describe('ProfileService', () => {
  let profileService;
  let mockProfileModel;
  let mockUserModel;
  let mockUserService;

  // Setup mock data
  const mockUser = {
    _id: 'user123',
    username: 'testuser',
    email: 'test@example.com',
    fullname: 'Test User',
    email_verified: true,
    avatar: 'avatar.jpg',
    role: 'role123',
    save: jest.fn().mockImplementation(() => Promise.resolve({ _doc: mockUser }))
  };

  const mockProfile = {
    _id: 'profile123',
    user_id: 'user123',
    nicknames: [],
    bio: 'Test bio',
    gender: 'male',
    date_of_birth: '1990-01-01',
    avatars: [],
    cover_photos: [],
    emails: ['test@example.com'],
    phones: [],
    addresses: [],
    socials: [],
    workplaces: [],
    educations: [],
    save: jest.fn().mockImplementation(() => Promise.resolve({ _doc: mockProfile }))
  };

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    const createChainableMock = () => {
      const mock = jest.fn();
      mock.mockReturnValue({
        lean: jest.fn().mockReturnValue(Promise.resolve(null))
      });
      return mock;
    };

    // Create mock models
    mockProfileModel = {
      findOne: createChainableMock(),
      create: jest.fn(),
      findById: createChainableMock(),
      findByIdAndUpdate: jest.fn(),
      deleteOne: jest.fn(),
      aggregate: jest.fn(),
    };

    mockUserModel = {
      findOne: createChainableMock(),
      findById: createChainableMock(),
    };

    // Setup service with mock models
    profileService = new ProfileService();
    profileService.profileModel = mockProfileModel;
    profileService.userModel = mockUserModel;
    mockUserService = new UserService();
    profileService.userService = mockUserService;

    // Setup default mock implementations
    MongooseUtil.convertToMongooseObjectIdType.mockImplementation(id => id);
  });

  describe('createNewProfile', () => {
    const newProfileData = {
      user_id: 'user123',
      emails: ['test@example.com'],
      bio: 'Test bio',
      gender: 'male',
      date_of_birth: '1990-01-01',
      avatars: [],
      cover_photos: [],
      phones: [],
      addresses: [],
      socials: [],
      workplaces: [],
      educations: []
    };

    it('should create new profile successfully', async () => {
      mockUserModel.findById.mockResolvedValue(mockUser);
      mockProfileModel.findOne.mockResolvedValue(null);
      mockProfileModel.create.mockResolvedValue(mockProfile);

      const result = await profileService.createNewProfile(newProfileData);

      expect(mockUserModel.findById).toHaveBeenCalledWith('user123');
      expect(mockProfileModel.findOne).toHaveBeenCalledWith({ user_id: 'user123' });
      expect(mockProfileModel.create).toHaveBeenCalled();
      expect(result).toEqual({
        ...ProfileFilter.makeBasicFilter(mockProfile),
        user: UserFilter.makeBasicFilter(mockUser),
        user_id: undefined,
      });
    });

    it('should throw error if user not found', async () => {
      mockUserModel.findById.mockResolvedValue(null);

      await expect(profileService.createNewProfile(newProfileData))
        .rejects
        .toThrow(new NotFoundResponse('User not found', 1050128));
    });

    it('should throw error if profile already exists', async () => {
      mockUserModel.findById.mockResolvedValue(mockUser);
      mockProfileModel.findOne.mockResolvedValue(mockProfile);

      await expect(profileService.createNewProfile(newProfileData))
        .rejects
        .toThrow(new ConflictResponse('Profile already exists', 1050129));
    });

    it('should throw error if email already in use', async () => {
      mockUserModel.findById.mockResolvedValue(mockUser);
      mockProfileModel.findOne.mockResolvedValue(null);
      mockUserModel.findOne.mockResolvedValue(mockUser);

      await expect(profileService.createNewProfile({ ...newProfileData, emails: ['new@example.com'] }))
        .rejects
        .toThrow(new ConflictResponse('Email already in use', 1050130));
    });
  });

  describe('getProfileList', () => {
    const mockQuery = {
      limit: 10,
      page: 1,
      search: 'test',
      sort: 'username',
      sortOrder: 1
    };

    it('should get profile list successfully', async () => {
      const mockAggregateResult = [{
        results: [mockProfile],
        totalCount: [{ count: 1 }]
      }];

      mockProfileModel.aggregate.mockResolvedValue(mockAggregateResult);

      const result = await profileService.getProfileList(mockQuery);

      expect(mockProfileModel.aggregate).toHaveBeenCalled();
      expect(result).toEqual({
        data: mockAggregateResult[0].results,
        total: mockAggregateResult[0].totalCount[0] ? mockAggregateResult[0].totalCount[0].count : 0,
      });
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockProfileModel.aggregate.mockRejectedValue(new Error('Unexpected error'));

      await expect(profileService.getProfileList(mockQuery))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('getProfileById', () => {
    it('should return profile by id successfully', async () => {
      mockProfileModel.findById().lean.mockResolvedValue(mockProfile);
      mockUserService.getUserById.mockResolvedValue(mockUser);

      const result = await profileService.getProfileById('profile123');

      expect(mockProfileModel.findById).toHaveBeenCalledWith('profile123');
      expect(mockUserService.getUserById).toHaveBeenCalledWith(mockProfile.user_id);
      expect(result).toBeDefined();
    });

    it('should throw error if profile not found', async () => {
      mockProfileModel.findById().lean.mockResolvedValue(null);

      await expect(profileService.getProfileById('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Profile not found', 1050303));
    });

    it('should throw error if user not found', async () => {
      mockProfileModel.findById().lean.mockResolvedValue(mockProfile);
      mockUserService.getUserById.mockResolvedValue(null);

      await expect(profileService.getProfileById('profile123'))
        .rejects
        .toThrow(new ConflictResponse('Something went wrong', 1050304));

      expect(mockUserService.getUserById).toHaveBeenCalledWith(mockProfile.user_id);
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockProfileModel.findById().lean.mockRejectedValue(new Error('Unexpected error'));

      await expect(profileService.getProfileById('profile123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('updateProfile', () => {
    const updateData = {
      nickname: 'newnickname',
      bio: 'New bio',
      gender: 'female',
      date_of_birth: '1991-01-01',
      avatar: 'newavatar.jpg',
      cover_photo: 'newcover.jpg',
      email: 'new@example.com',
      phone: '1234567890',
      address: 'New address',
      social: 'new_social',
      workplace: 'new_workplace',
      education: 'new_education'
    };

    it('should successfully update profile', async () => {
      mockProfileModel.findById.mockResolvedValue(mockProfile);
      mockUserService.getUserById.mockResolvedValue(mockUser);
      mockUserModel.findOne.mockResolvedValue(null);

      const result = await profileService.updateProfile('profile123', updateData);

      expect(mockProfileModel.findById).toHaveBeenCalledWith('profile123');
      expect(mockUserService.getUserById).toHaveBeenCalledWith(mockProfile.user_id);
      expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: updateData.email });
      expect(mockProfile.save).toHaveBeenCalled();
      expect(result).toBeDefined();
    });

    it('should throw error if profile not found', async () => {
      mockProfileModel.findById.mockResolvedValue(null);

      await expect(profileService.updateProfile('nonexistent', updateData))
        .rejects
        .toThrow(new NotFoundResponse('Profile not found', 1050426));
    });

    it('should throw error if user not found', async () => {
      mockProfileModel.findById.mockResolvedValue(mockProfile);
      mockUserService.getUserById.mockResolvedValue(null);

      await expect(profileService.updateProfile('profile123', updateData))
        .rejects
        .toThrow(new ConflictResponse('Something went wrong', 1050427));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockProfileModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(profileService.updateProfile('profile123', updateData))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });

  describe('deleteProfile', () => {
    it('should successfully delete profile', async () => {
      mockProfileModel.findById.mockResolvedValue(mockProfile);
      mockUserService.getUserById.mockResolvedValue(mockUser);
      mockProfileModel.deleteOne.mockResolvedValue({ deletedCount: 1 });

      await profileService.deleteProfile('profile123');

      expect(mockProfileModel.findById).toHaveBeenCalledWith('profile123');
      expect(mockProfileModel.deleteOne).toHaveBeenCalledWith({ _id: mockProfile._id });
    });

    it('should throw error if profile not found', async () => {
      mockProfileModel.findById.mockResolvedValue(null);

      await expect(profileService.deleteProfile('nonexistent'))
        .rejects
        .toThrow(new NotFoundResponse('Profile not found', 1050503));
    });

    it('should throw error if user not found', async () => {
      mockProfileModel.findById.mockResolvedValue(mockProfile);
      mockUserService.getUserById.mockResolvedValue(null);

      await expect(profileService.deleteProfile('profile123'))
        .rejects
        .toThrow(new ConflictResponse('Something went wrong', 1050504));
    });

    it('should throw error if an unexpected error is occurred', async () => {
      mockProfileModel.findById.mockRejectedValue(new Error('Unexpected error'));

      await expect(profileService.deleteProfile('profile123'))
        .rejects
        .toThrow(new Error('Unexpected error'));
    });
  });
});