const validGetAccessOwnerIdsRequest = {
    params: { id: 'jest-client-id' }
};
const validGetAccessOwnerIdsResult = {
    owners: ['jest-client-id', 'jest-client-id-2']
}

const validSignupPayload = {
    email: 'jest@test.com',
    password: '123456',
}
const validSignupResult = { ...validSignupPayload, id: '1' };

const validLoginPayload = { ...validSignupPayload }
const validLoginResult = { user: { ...validSignupResult }, accessToken: 'jest-access-token', refreshToken: 'jest-refresh-token' };

const validInvokeNewTokenRequest = {
    headers: {
        'x-client-id': 'jest-client-id',
        'authorization': 'Bearer jest-access-token',
    },
    body: {
        refreshToken: 'jest-refresh-token',
    }
}
const validInvokeNewTokenResult = {
    error: false,
    data: {
        userId: 'jest-client-id',
        refreshToken: 'jest-refresh-token',
        accessToken: 'jest-access-token',
    },
}

const validVerifyEmailPayload = {
    email: 'jest@tester.com',
}
const validVerifyEmailResult = validVerifyEmailPayload;

const validVerifyOTPPayload = {
    email: 'jest@tester.com',
    otp: '123456',
}
const validVerifyOTPResult = {
    error: false,
    data: {
        userEmail: 'jest@tester.com',
        otp: '123456'
    }
}

const validateResetPasswordRequest = {
    headers: { ...validInvokeNewTokenRequest.headers },
    body: {
        newPassword: '123456',
        confirmNewPassword: '123456',
    }
}

const validResetPasswordResult = {
    error: false,
    data: {
        userId: 'jest-client-id',
        resetPasswordToken: 'jest-access-token',
        newPassword: '123456',
    }
}


const validLogoutRequest = {
    user: { id: 'jest-client-id' }
}

const mockUserResponse = {
    _id: 'jest-user-id',
    email: 'jest@tester.com',
    username: 'jest tester',
    password: 'hashedPassword',
    fullname: 'Jest Tester',
    role: 'User',
    email_verified: true,
    avatar: 'avatar.jpg',
    slug: 'test-slug',
    type_login: 'local',
}

const mockAccessResponse = {
    _id: 'jest-access-id',
    user_id: 'jest-user-id',
    public_key: 'publicKey',
    private_key: 'privateKey',
    refresh_token: 'jest-refresh-token',
    otp: {
        code: '123456',
        expiredAt: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes from now
    },
    otp_count: 0,
    last_otp_sent: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
    otp_reset_password: {
        code: '123456',
        expiredAt: new Date(Date.now() + 5 * 60 * 1000), // 5 minutes from now
    },
    reset_password_token: 'jest-reset-password-token',
    otp_reset_password_count: 0,
    last_otp_reset_password_sent: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
}

const mockRoleResponse = {
    _id: 'jest-role-id',
    name: 'User',
    description: 'User role',
    status: 'active',
    grants: [],
}

const mockInvokeNewTokenParameters = {
    userId: 'jest-client-id',
    refreshToken: 'jest-refresh-token',
    accessToken: 'jest-access-token',
    refresh_token_used: [{ token: 'jest-old-refresh-token-1' }, { token: 'jest-old-refresh-token-2' }]
}


const mockLoginWithFacebookParameters = {
    facebook_id: 'jest-facebook-id',
    email: mockUserResponse.email,
    username: mockUserResponse.username,
    type_login: 'facebook'
}

module.exports = {
    validGetAccessOwnerIdsRequest,
    validGetAccessOwnerIdsResult,
    validSignupPayload,
    validSignupResult,
    validLoginPayload,
    validLoginResult,
    validVerifyEmailPayload,
    validVerifyEmailResult,
    validInvokeNewTokenRequest,
    validInvokeNewTokenResult,
    validateResetPasswordRequest,
    validResetPasswordResult,
    validVerifyOTPPayload,
    validVerifyOTPResult,
    validLogoutRequest,
    mockInvokeNewTokenParameters,
    mockLoginWithFacebookParameters,

    mockUserResponse,
    mockAccessResponse,
    mockRoleResponse,
}