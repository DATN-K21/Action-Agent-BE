/**
 * 
 * @param {Number} timeInMilliseconds Default is 5 minutes
 */
const generateOtpCode = (timeInMilliseconds = 5 * 60 * 1000) => {
    const otpPasscode = Math.floor(100000 + Math.random() * 900000);
    const expiredCode = new Date(new Date().getTime() + timeInMilliseconds);
    const otp = {
        code: otpPasscode,
        expiredAt: expiredCode,
    }
    return otp;
}

module.exports = {
    generateOtpCode,
};