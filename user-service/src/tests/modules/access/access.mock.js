
const validSignupPayload = {
    email: 'jest@test.com',
    password: '123456',
}

const validLoginPayload = { ...validSignupPayload }

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

const validLogoutRequest = {
    user: { id: 'jest-client-id' }
}

module.exports = {
    validSignupPayload,
    validLoginPayload,
    validInvokeNewTokenRequest,
    validInvokeNewTokenResult,
    validateResetPasswordRequest,
    validResetPasswordResult,
    validVerifyOTPPayload,
    validVerifyOTPResult,
    validLogoutRequest,
}