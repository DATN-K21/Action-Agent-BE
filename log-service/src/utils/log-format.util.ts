import * as winston from 'winston';

export const logFormat = winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message, context, service, ...metadata }) => {
        return JSON.stringify({
            timestamp,
            level,
            message,
            context,
            service: service || 'unknown-service',
            metadata,
        });
    }),
);
