const UserService = require('../../modules/user/user.service');
const { ConflictResponse } = require('../../response/error');
const BcryptHelper = require('../../helpers/bcrypt.helper');
const { generateRandomString, generateRSAKeysForAccess } = require('../../utils/crypto.util');
const MongooseUtil = require('../../utils/mongoose.util');

// Mock dependencies
jest.mock('../../helpers/bcrypt.helper');
jest.mock('../../utils/crypto.util');
jest.mock('../../utils/mongoose.util');

describe('UserService', () => {
	let userService;
	let mockUserModel;
	let mockRoleModel;
	let mockAccessModel;

	// Setup mock data
	const mockUser = {
		_id: 'user123',
		username: 'testuser',
		email: 'test@example.com',
		password: 'hashedPassword',
		fullname: 'Test User',
		role: 'role123',
		email_verified: true,
		avatar: 'avatar.jpg',
		slug: 'test-slug',
		save: jest.fn().mockImplementation(() => Promise.resolve({ _doc: mockUser }))
	};

	const mockRole = {
		_id: 'role123',
		name: 'User'
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
		mockUserModel = {
			findOne: createChainableMock(),
			create: jest.fn(),
			findById: createChainableMock(),
			findByIdAndUpdate: jest.fn(),
			deleteOne: jest.fn(),
			aggregate: jest.fn(),
		};

		mockRoleModel = {
			findOne: createChainableMock(),
			findById: createChainableMock(),
		};

		mockAccessModel = {
			create: jest.fn(),
			deleteOne: jest.fn(),
		};

		// Setup service with mock models
		userService = new UserService();
		userService.userModel = mockUserModel;
		userService.roleModel = mockRoleModel;
		userService.accessModel = mockAccessModel;

		// Setup default mock implementations
		BcryptHelper.hash.mockResolvedValue('hashedPassword');
		generateRandomString.mockReturnValue('random123');
		generateRSAKeysForAccess.mockReturnValue({
			privateKey: 'privateKey',
			publicKey: 'publicKey'
		});
		MongooseUtil.convertToMongooseObjectIdType.mockImplementation(id => id);
	});

	describe('createNewUser', () => {
		const newUserData = {
			username: 'testuser',
			email: 'test@example.com',
			password: 'password123',
			fullname: 'Test User',
			email_verified: true,
			avatar: 'avatar.jpg'
		};

		it('should create new user successfully', async () => {
			mockUserModel.findOne.mockResolvedValue(null);
			mockRoleModel.findOne().lean.mockResolvedValue(mockRole);
			mockUserModel.create.mockResolvedValue(mockUser);
			mockUserModel.findByIdAndUpdate.mockResolvedValue(mockUser);

			const result = await userService.createNewUser(newUserData);

			expect(mockUserModel.findOne).toHaveBeenCalledWith({ email: newUserData.email });
			expect(mockRoleModel.findOne).toHaveBeenCalledWith({ name: 'User' });
			expect(BcryptHelper.hash).toHaveBeenCalledWith(newUserData.password);
			expect(mockUserModel.create).toHaveBeenCalled();
			expect(mockAccessModel.create).toHaveBeenCalled();
			expect(result).toEqual(mockUser);
		});

		it('should throw error if email already exists', async () => {
			mockUserModel.findOne.mockResolvedValue(mockUser);

			await expect(userService.createNewUser(newUserData))
				.rejects
				.toThrow(new ConflictResponse('Email already exists', 1040108));
		});

		it('should throw error if User role not found', async () => {
			mockUserModel.findOne.mockResolvedValue(null);
			mockRoleModel.findOne().lean.mockResolvedValue(null);

			await expect(userService.createNewUser(newUserData))
				.rejects
				.toThrow(new ConflictResponse('User role not found', 1040110));
		});

		it('should throw error if an unexpected error is occurred', async () => {
			mockUserModel.findOne.mockRejectedValue(new Error('Unexpected error'));

			await expect(userService.createNewUser(newUserData))
				.rejects
				.toThrow(new Error('Unexpected error'));
		});
	});

	describe('getUserList', () => {
		const mockQuery = {
			limit: 10,
			page: 1,
			search: 'test',
			sort: 'username',
			sortOrder: 1
		};

		it('should get user list successfully', async () => {
			const mockAggregateResult = [{
				results: [mockUser],
				totalCount: [{ count: 1 }]
			}];

			mockUserModel.aggregate.mockResolvedValue(mockAggregateResult);

			const result = await userService.getUserList(mockQuery);

			expect(mockUserModel.aggregate).toHaveBeenCalled();
			expect(result).toEqual({
				data: mockAggregateResult[0].results,
				total: mockAggregateResult[0].totalCount[0].count
			});
		});

		it('should throw error if an unexpected error is occurred', async () => {
			mockUserModel.aggregate.mockRejectedValue(new Error('Unexpected error'));

			await expect(userService.getUserList(mockQuery))
				.rejects
				.toThrow(new Error('Unexpected error'));
		});
	});

	describe('getUserById', () => {
		it('should return user by id successfully', async () => {
			mockUserModel.findById().lean.mockResolvedValue(mockUser);
			mockRoleModel.findById.mockResolvedValue(mockRole);

			const result = await userService.getUserById('user123');

			expect(mockUserModel.findById).toHaveBeenCalledWith('user123');
			expect(mockRoleModel.findById).toHaveBeenCalledWith(mockUser.role);
			expect(result).toBeDefined();
		});

		it('should throw error if user not found', async () => {
			mockUserModel.findById().lean.mockResolvedValue(null);

			await expect(userService.getUserById('nonexistent'))
				.rejects
				.toThrow(new ConflictResponse('User not found', 1040303));
		});

		it('should throw error if role not found', async () => {
			mockUserModel.findById().lean.mockResolvedValue(mockUser);
			mockRoleModel.findById.mockResolvedValue(null);

			await expect(userService.getUserById('user123'))
				.rejects
				.toThrow(new ConflictResponse('Something went wrong', 1040304));

			expect(mockRoleModel.findById).toHaveBeenCalledWith(mockUser.role);
		});

		it('should throw error if an unexpected error is occurred', async () => {
			mockUserModel.findById().lean.mockRejectedValue(new Error('Unexpected error'));

			await expect(userService.getUserById('user123'))
				.rejects
				.toThrow(new Error('Unexpected error'));
		});
	});

	describe('updateUser', () => {
		const updateData = {
			username: 'newusername',
			fullname: 'New Name',
			role: 'newrole123'
		};

		it('should successfully update user', async () => {
			mockUserModel.findById.mockResolvedValue(mockUser);
			mockRoleModel.findById().lean.mockResolvedValue(mockRole);

			const result = await userService.updateUser('user123', updateData);

			expect(mockUserModel.findById).toHaveBeenCalledWith('user123');
			expect(mockUser.save).toHaveBeenCalled();
			expect(result).toBeDefined();
		});

		it('should throw error if user not found', async () => {
			mockUserModel.findById.mockResolvedValue(null);

			await expect(userService.updateUser('nonexistent', updateData))
				.rejects
				.toThrow(new ConflictResponse('User not found', 1040408));
		});

		it('should throw error if role not found', async () => {
			mockUserModel.findById.mockResolvedValue(mockUser);
			mockRoleModel.findById().lean.mockResolvedValue(null);

			await expect(userService.updateUser('user123', updateData))
				.rejects
				.toThrow(new ConflictResponse('Role not found', 1040409));
		});

		it('should throw error if an unexpected error is occurred', async () => {
			mockUserModel.findById.mockRejectedValue(new Error('Unexpected error'));

			await expect(userService.updateUser('user123', updateData))
				.rejects
				.toThrow(new Error('Unexpected error'));
		});
	});

	describe('deleteUser', () => {
		it('should successfully delete user', async () => {
			mockUserModel.findById.mockResolvedValue(mockUser);
			mockUserModel.deleteOne.mockResolvedValue({ deletedCount: 1 });
			mockAccessModel.deleteOne.mockResolvedValue({ deletedCount: 1 });

			const result = await userService.deleteUser('user123');

			expect(mockUserModel.findById).toHaveBeenCalledWith('user123');
			expect(mockAccessModel.deleteOne).toHaveBeenCalled();
			expect(mockUserModel.deleteOne).toHaveBeenCalledWith({ _id: mockUser._id });
			expect(result).toEqual({ deletedCount: 1 });
		});

		it('should throw error if user not found', async () => {
			mockUserModel.findById.mockResolvedValue(null);

			await expect(userService.deleteUser('nonexistent'))
				.rejects
				.toThrow(new ConflictResponse('User not found', 1040503));
		});
	});

	it('should throw error if an unexpected error is occurred', async () => {
		mockUserModel.findById.mockRejectedValue(new Error('Unexpected error'));

		await expect(userService.deleteUser('user123'))
			.rejects
			.toThrow(new Error('Unexpected error'));
	});
});