const nodemailer = require("nodemailer");
const emailConfig = require('../configs/email.config');

class EmailHelper {

    static async sendEmail(emailAddress, otpPasscode) {
        const transporter = nodemailer.createTransport({
            host: "smtp.gmail.com",
            port: 587,
            secure: false,
            auth: {
                user: emailConfig.user,
                pass: emailConfig.pass,
            },
        });

        const otpMessage = `
            <p>Thank you for registering an account on My AI Assistant Application. Your OTP code is:</p>
            <h2>${otpPasscode}</h2>
            <p>Please enter this code to verify your email address.</p>
            <strong>Note: The One-Time Password (OTP) is valid for 5 minutes.</strong>
        `;
        const info = await transporter.sendMail({
            from: '"My AI Assistant" <myaiassistant24@gmail.com>', // sender address
            to: emailAddress,
            subject: "[My AI Assistant] Verify Email", // Subject line
            text: `Your OTP code is: ${otpPasscode}`, // plain text body
            html: otpMessage, // html body
        });
        if (info.accepted.length > 0) {
            return info;
        } else {
            console.log("Failed to send OTP email.");
            return null;
        }
    }

    static async sendResetPasswordEmail(emailAddress, otpPasscode) {
        const transporter = nodemailer.createTransport({
            host: "smtp.gmail.com",
            port: 587,
            secure: false,
            auth: {
                user: emailConfig.user,
                pass: emailConfig.pass,
            },
        });

        const otpMessage = `
            <p>You have requested to reset your password on My AI Assistant Application. Your OTP code is:</p>
            <h2>${otpPasscode}</h2>
            <p>Please enter this code to reset your password.</p>
            <strong>Note: The One-Time Password (OTP) is valid for 5 minutes.</strong>
        `;
        const info = await transporter.sendMail({
            to: emailAddress,
            subject: "[My AI Assistant] Verify Email", // Subject line
            text: `Your OTP code is: ${otpPasscode}`, // plain text body
            html: otpMessage, // html body
        });
        if (info.accepted.length > 0) {
            return info;
        } else {
            console.log("Failed to send OTP email.");
            return null;
        }
    }

    static async sendActivationEmail(emailAddress, activationToken) {
        const transporter = nodemailer.createTransport({
            host: "smtp.gmail.com",
            port: 587,
            secure: false,
            auth: {
                user: emailConfig.user,
                pass: emailConfig.pass,
            },
        });

        const activationMessage = `
            <p>Thank you for registering an account on My AI Assistant Application. Please click the link below to activate your account:</p>
            <a href="${process.env.CLIENT_URL}/account-activation?token=${activationToken}">Activate Account</a><br>
            <strong>Note: The activation link is valid for 15 minutes.</strong>
        `;
        const info = await transporter.sendMail({
            to: emailAddress,
            subject: "[My AI Assistant] Activate Account", // Subject line
            html: activationMessage, // html body
        });
        if (info.accepted.length > 0) {
            return info;
        } else {
            console.log("Failed to send activation email.");
            return null;
        }
    }
}

module.exports = EmailHelper;
