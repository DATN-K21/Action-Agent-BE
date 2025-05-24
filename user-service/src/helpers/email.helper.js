const nodemailer = require("nodemailer");

class EmailHelper {
    constructor(transportConfig) {
        // Initialize the transporter with the provided transport configuration
        this.transporter = nodemailer.createTransport(transportConfig);
    }

    /**
     * Send an email with the specified parameters.
     * @param {string} from - Sender's email address.
     * @param {string} to - Recipient's email address.
     * @param {string} subject - Subject of the email.
     * @param {string} text - Plain text content of the email.
     * @param {string} html - HTML content of the email.
     * @returns {Promise<object>} - Information about the sent email.
     */
    async sendEmail({ from, to, subject, text, html }) {
        try {
            const info = await this.transporter.sendMail({
                from,
                to,
                subject,
                text,
                html,
            });

            if (info.accepted.length > 0) {
                // console.log("Email sent successfully:", info);
                return info;
            } else {
                // console.log("Failed to send email.");
                return null;
            }
        } catch (error) {
            // console.error("Error sending email:", error);
            return null;
        }
    }
}

module.exports = EmailHelper;