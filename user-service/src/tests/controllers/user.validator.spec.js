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
	});
});