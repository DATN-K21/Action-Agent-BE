const UserValidator = require("../../modules/user/user.validator");

describe("UserValidator", () => {
	beforeEach(() => {
		// Reset all mocks
		jest.clearAllMocks();
	});

	describe("validateCreateNewUser", () => {
		const validPayload = {
			email: "test@jest.com",
			password: "password",
			email_verified: "true",
			username: "jest",
			fullname: "Jest Tester",
			avatar: "https://jest.com/avatar.jpg",
		}
		it("should validate create new user successfully", async () => {
			const req = { body: validPayload };
			const result = UserValidator.validateCreateNewUser(req);

			expect(result).toEqual({
				error: false,
				data: validPayload
			});
		});

		it("should validate create new user with empty email", async () => {
			const req = { body: { ...validPayload, email: "" } };
			const result = UserValidator.validateCreateNewUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040101,
				message: "Email is required"
			});
		});

		it("should validate create new user with invalid email", async () => {
			const req = { body: { ...validPayload, email: "invalid-email" } };
			const result = UserValidator.validateCreateNewUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040102,
				message: "Email is invalid"
			});
		});

		it("should validate create new user with empty password", async () => {
			const req = { body: { ...validPayload, password: "" } };
			const result = UserValidator.validateCreateNewUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040103,
				message: "Password is required"
			});
		});

		it("should validate create new user with short password", async () => {
			const req = { body: { ...validPayload, password: "12" } };
			const result = UserValidator.validateCreateNewUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040104,
				message: "Password must be at least 3 characters long"
			});
		});

		it("should validate create new user with invalid email_verified", async () => {
			const req = { body: { ...validPayload, email_verified: "invalid-boolean" } };
			const result = UserValidator.validateCreateNewUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040107,
				message: "Email verification must be a boolean"
			});
		});
	});

	describe("validateGetUserList", () => {
		const validQuery = {
			limit: "10",
			page: "1",
			search: "test",
			sort: "username",
			sortOrder: "1",
		};
		const expectedFilterResult = {
			filter: {
				limit: 10,
				page: 1,
				search: "test",
				sort: "username",
				sortOrder: 1,
			}
		};

		it("should validate get user list successfully", async () => {
			const req = { query: validQuery };
			const result = UserValidator.validateGetUserList(req);

			expect(result).toEqual({
				error: false,
				data: { filter: expectedFilterResult.filter }
			});
		});

		it("should validate get user list with invalid limit", async () => {
			const req = { query: { ...validQuery, limit: "invalid" } };
			const result = UserValidator.validateGetUserList(req);

			expect(result).toEqual({
				error: true,
				code: 1040201,
				message: "Limit must be an integer"
			});
		});

		it("should validate get user list with invalid page", async () => {
			const req = { query: { ...validQuery, page: "invalid" } };
			const result = UserValidator.validateGetUserList(req);

			expect(result).toEqual({
				error: true,
				code: 1040202,
				message: "Page must be an integer"
			});
		});

		it("should validate get user list with invalid sort", async () => {
			const req = { query: { ...validQuery, sort: "invalid" } };
			const result = UserValidator.validateGetUserList(req);

			expect(result).toEqual({
				error: true,
				code: 1040203,
				message: "Sorted attribute is invalid"
			});
		});

		it("should validate get user list with invalid sort order", async () => {
			const req = { query: { ...validQuery, sortOrder: "invalid" } };
			const result = UserValidator.validateGetUserList(req);

			expect(result).toEqual({
				error: true,
				code: 1040205,
				message: "Sort order must be ascending (1) or descending (-1)"
			});
		});

		it("should validate get user list with sort order but no sort", async () => {
			const req = { query: { ...validQuery, sort: "", sortOrder: "1" } };
			const result = UserValidator.validateGetUserList(req);

			expect(result).toEqual({
				error: true,
				code: 1040204,
				message: "Sort order can only be used when sort is given"
			});
		});
	});

	describe("validateGetUserById", () => {
		const validParams = {
			id: "507f1f77bcf86cd799439011"
		};

		it("should validate get user by id successfully", async () => {
			const req = { params: validParams };
			const result = UserValidator.validateGetUserById(req);

			expect(result).toEqual({
				error: false,
				data: { userId: validParams.id }
			});
		});

		it("should validate get user by id with empty id", async () => {
			const req = { params: { id: "" } };
			const result = UserValidator.validateGetUserById(req);

			expect(result).toEqual({
				error: true,
				code: 1040301,
				message: "User ID is required"
			});
		});

		it("should validate get user by id with invalid mongo id", async () => {
			const req = { params: { id: "invalid-id" } };
			const result = UserValidator.validateGetUserById(req);

			expect(result).toEqual({
				error: true,
				code: 1040302,
				message: "User ID is invalid"
			});
		});
	})

	describe("validateUpdateUser", () => {
		const fullValidPayload = {
			password: "password",
			email_verified: "true",
			username: "jest",
			fullname: "Jest Tester",
			avatar: "https://jest.com/avatar.jpg",
		};
		const validParams = {
			id: "507f1f77bcf86cd799439011"
		};

		it("should validate update user successfully", async () => {
			const req = { body: fullValidPayload, params: validParams };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: false,
				data: { ...fullValidPayload, userId: validParams.id }
			});
		});

		it("should validate update user with empty id", async () => {
			const req = { body: fullValidPayload, params: { id: "" } };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040401,
				message: "User ID is required"
			});
		});

		it("should validate update user with invalid mongo id", async () => {
			const req = { body: fullValidPayload, params: { id: "invalid-id" } };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040402,
				message: "User ID is invalid"
			});
		});

		it("should validate update user with empty body", async () => {
			const req = { body: {}, params: validParams };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040403,
				message: "No data given to update"
			});
		});

		it("should validate update user with email changing effort", async () => {
			const req = { body: { ...fullValidPayload, email: "test@jest.com" }, params: validParams };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040404,
				message: "Email is irreplaceable"
			});
		});

		it("should validate update user with short password", async () => {
			const req = { body: { ...fullValidPayload, password: "12" }, params: validParams };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040405,
				message: "Password must be at least 3 characters long"
			});
		});

		it("should validate update user with invalid email_verified", async () => {
			const req = { body: { ...fullValidPayload, email_verified: "invalid-boolean" }, params: validParams };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040407,
				message: "Email verification must be a boolean"
			});
		});

		it("should validate update user with invalid role id", async () => {
			const req = { body: { ...fullValidPayload, roleId: "invalid-id" }, params: validParams };
			const result = UserValidator.validateUpdateUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040406,
				message: "Role ID is invalid"
			});
		});
	});

	describe("validateDeleteUser", () => {
		const validParams = {
			id: "507f1f77bcf86cd799439011"
		};

		it("should validate delete user successfully", async () => {
			const req = { params: validParams };
			const result = UserValidator.validateDeleteUser(req);

			expect(result).toEqual({
				error: false,
				data: { userId: validParams.id }
			});
		});

		it("should validate delete user with empty id", async () => {
			const req = { params: { id: "" } };
			const result = UserValidator.validateDeleteUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040501,
				message: "User ID is required"
			});
		});

		it("should validate delete user with invalid mongo id", async () => {
			const req = { params: { id: "invalid-id" } };
			const result = UserValidator.validateDeleteUser(req);

			expect(result).toEqual({
				error: true,
				code: 1040502,
				message: "User ID is invalid"
			});
		});
	});
});