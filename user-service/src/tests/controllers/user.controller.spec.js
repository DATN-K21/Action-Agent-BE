const UserController = require("../../modules/user/user.controller");
const UserService = require("../../modules/user/user.service");
const UserValidator = require("../../modules/user/user.validator");
const { BadRequestResponse } = require("../../response/error");
const { MongooseError } = require("mongoose");

jest.mock("../../modules/user/user.service");
jest.mock("../../modules/user/user.validator");

describe("UserController", () => {
  let userService;
  let res;

  beforeEach(() => {
    userService = new UserService();
    UserController.userService = userService;

    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    };
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe("getUserOwnerIds", () => {
    const mockUserId = "123";
    const expectedUserOwnerIds = ["456", "789"];

    it("should get user owner ids successfully for specific user id", async () => {
      const req = { params: { id: mockUserId } };
      userService.getUserById.mockResolvedValue({ owners: expectedUserOwnerIds });
      const result = await UserController.getUserOwnerIds(req);
      expect(result).toEqual(expectedUserOwnerIds);
    });

    it("should return empty array if user id is not provided", async () => {
      const req = { params: {} };
      const result = await UserController.getUserOwnerIds(req);
      expect(result).toEqual([]);
    });

    it("should throw an error if an unexpected error is occurred", async () => {
      const req = { params: { id: mockUserId } };
      userService.getUserById.mockRejectedValue(new Error("Unexpected error"));
      await expect(UserController.getUserOwnerIds(req, res)).rejects.toThrowError(Error);
    });
  });

  describe("createNewUser", () => {
    const validCreateNewUserPayload = {
      username: "testUser",
      email: "test@example.com",
      password: "password123",
      fullname: "Test User",
      email_verified: true,
      avatar: "test-avatar.png",
    };
    const { password, ...expectedResult } = validCreateNewUserPayload;

    it("should create new user successfully", async () => {
      const req = { body: validCreateNewUserPayload };

      // Mock validation and service methods
      UserValidator.validateCreateNewUser.mockReturnValue({ data: req.body });
      userService.createNewUser.mockResolvedValue({ id: "123", ...req.body });

      await UserController.createNewUser(req, res);

      expect(res.status).toHaveBeenCalledWith(201);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "Create new user success",
          code: 1040100,
          data: expect.objectContaining({ id: "123", ...expectedResult }),
        })
      );
    });

    it("should throw BadRequestResponse for invalid request", async () => {
      const req = { body: { ...validCreateNewUserPayload, email: undefined } };
      UserValidator.validateCreateNewUser.mockReturnValue({
        error: true,
        message: "Invalid data",
        code: 400,
      });

      await expect(UserController.createNewUser(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw BadRequestResponse if a Mongoose Error is occurred", async () => {
      const req = { body: validCreateNewUserPayload };

      UserValidator.validateCreateNewUser.mockReturnValue({ data: req.body });
      userService.createNewUser.mockRejectedValue(new MongooseError("Something went wrong", 1040110));

      await expect(UserController.createNewUser(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw error if an unexpected error is occurred", async () => {
      const req = { body: validCreateNewUserPayload };

      UserValidator.validateCreateNewUser.mockReturnValue({ data: req.body });
      userService.createNewUser.mockRejectedValue(new Error("Unexpected error"));

      await expect(UserController.createNewUser(req, res)).rejects.toThrowError(Error);
    });
  });

  describe("getUserList", () => {
    const validGetUserListQuery = {
      page: 1,
      limit: 10,
      search: "test",
      sort: "username",
      sortOrder: 1,
    };
    const expectedServiceResult = {
      data: [{ id: "1", username: "test1" }, { id: "2", username: "test2" }, { id: "3", username: "test3" }],
      total: 3,
    }

    it("should get user list successfully", async () => {
      const req = { query: validGetUserListQuery };

      UserValidator.validateGetUserList.mockReturnValue({ data: req.query });
      userService.getUserList.mockResolvedValue(expectedServiceResult);

      await UserController.getUserList(req, res);

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "Get user list success",
          data: expectedServiceResult.data,
          metadata: expect.objectContaining({ total: 3 }),
        })
      );
    });

    it("should throw BadRequestResponse for invalid request", async () => {
      const req = { query: { ...validGetUserListQuery, limit: "invalid" } };
      UserValidator.validateGetUserList.mockReturnValue({
        error: true,
        message: "Invalid data",
        code: 400,
      });

      await expect(UserController.getUserList(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw BadRequestResponse if a Mongoose Error is occurred", async () => {
      const req = { query: validGetUserListQuery };

      UserValidator.validateGetUserList.mockReturnValue({ data: req.query });
      userService.getUserList.mockRejectedValue(new MongooseError("Something went wrong", 1040110));

      await expect(UserController.getUserList(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw error if an unexpected error is occurred", async () => {
      const req = { query: validGetUserListQuery };

      UserValidator.validateGetUserList.mockReturnValue({ data: req.body });
      userService.getUserList.mockRejectedValue(new Error("Unexpected error"));

      await expect(UserController.getUserList(req, res)).rejects.toThrowError(Error);
    });
  });

  describe("getUserById", () => {
    const mockUserId = "123";
    const mockUser = { id: mockUserId, username: "testUser", email: "test@jest.com" };

    it("should get user by id successfully", async () => {
      const req = { params: { id: mockUserId } };
      UserValidator.validateGetUserById.mockReturnValue({ data: req.params });
      userService.getUserById.mockResolvedValue(mockUser);

      await UserController.getUserById(req, res);

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "Get user by ID success",
          data: mockUser,
          code: 1040300,
        })
      );
    });

    it("should throw BadRequestResponse for invalid request", async () => {
      const req = { params: {} };
      UserValidator.validateGetUserById.mockReturnValue({
        error: true,
        message: "Invalid data",
        code: 400,
      });

      await expect(UserController.getUserById(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw BadRequestResponse if a Mongoose Error is occurred", async () => {
      const req = { params: { id: mockUserId } };

      UserValidator.validateGetUserById.mockReturnValue({ data: req.params });
      userService.getUserById.mockRejectedValue(new MongooseError("Something went wrong", 1040110));

      await expect(UserController.getUserById(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw error if an unexpected error is occurred", async () => {
      const req = { params: { id: mockUserId } };

      UserValidator.validateGetUserById.mockReturnValue({ data: req.params });
      userService.getUserById.mockRejectedValue(new Error("Unexpected error"));

      await expect(UserController.getUserById(req, res)).rejects.toThrowError(Error);
    });
  });

  describe("updateUser", () => {
    const mockUserId = "123";
    const mockUpdateUserPayload = { username: "newUsername" };
    const mockUpdatedUser = { id: mockUserId, ...mockUpdateUserPayload };

    it("should update user by id successfully", async () => {
      const req = { params: { id: mockUserId }, body: mockUpdateUserPayload };
      UserValidator.validateUpdateUser.mockReturnValue({ data: { userId: mockUserId, ...mockUpdateUserPayload } });
      userService.updateUser.mockResolvedValue(mockUpdatedUser);

      await UserController.updateUser(req, res);

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "Update user success",
          data: mockUpdatedUser,
          code: 1040400,
        })
      );
    });

    it("should throw BadRequestResponse for invalid request", async () => {
      const req = { params: { id: mockUserId }, body: {} };
      UserValidator.validateUpdateUser.mockReturnValue({
        error: true,
        message: "Invalid data",
        code: 400,
      });

      await expect(UserController.updateUser(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw BadRequestResponse if a Mongoose Error is occurred", async () => {
      const req = { params: { id: mockUserId }, body: mockUpdateUserPayload };

      UserValidator.validateUpdateUser.mockReturnValue({ data: { userId: mockUserId, ...mockUpdateUserPayload } });
      userService.updateUser.mockRejectedValue(new MongooseError("Something went wrong", 1040110));

      await expect(UserController.updateUser(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw error if an unexpected error is occurred", async () => {
      const req = { params: { id: mockUserId }, body: mockUpdateUserPayload };

      UserValidator.validateUpdateUser.mockReturnValue({ data: { userId: mockUserId, ...mockUpdateUserPayload } });
      userService.updateUser.mockRejectedValue(new Error("Unexpected error"));

      await expect(UserController.updateUser(req, res)).rejects.toThrowError(Error);
    });
  });

  describe("deleteUser", () => {
    const mockUserId = "123";
    const mockDeletedUser = { id: mockUserId, username: "testUser" };

    it("should delete user by id successfully", async () => {
      const req = { params: { id: mockUserId } };
      UserValidator.validateDeleteUser.mockReturnValue({ data: { userId: mockUserId } });
      userService.deleteUser.mockResolvedValue(mockDeletedUser);

      await UserController.deleteUser(req, res);

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({
          message: "Delete user success",
          data: { deleted: mockUserId },
          code: 1040500,
          metadata: mockDeletedUser,
        })
      );
    });

    it("should throw BadRequestResponse for invalid request", async () => {
      const req = { params: {} };
      UserValidator.validateDeleteUser.mockReturnValue({
        error: true,
        message: "Invalid data",
        code: 400,
      });

      await expect(UserController.deleteUser(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw BadRequestResponse if a Mongoose Error is occurred", async () => {
      const req = { params: { id: mockUserId } };

      UserValidator.validateDeleteUser.mockReturnValue({ data: { userId: mockUserId } });
      userService.deleteUser.mockRejectedValue(new MongooseError("Something went wrong", 1040110));

      await expect(UserController.deleteUser(req, res)).rejects.toThrowError(BadRequestResponse);
    });

    it("should throw error if an unexpected error is occurred", async () => {
      const req = { params: { id: mockUserId } };

      UserValidator.validateDeleteUser.mockReturnValue({ data: { userId: mockUserId } });
      userService.deleteUser.mockRejectedValue(new Error("Unexpected error"));

      await expect(UserController.deleteUser(req, res)).rejects.toThrowError(Error);
    });
  });
});


