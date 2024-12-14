import { Controller, Post, Body, Headers, Logger, Get } from '@nestjs/common';
import { LogService } from './log.service';

@Controller('logs')
export class LogController {
    private readonly logger = new Logger(LogController.name);
    constructor(private readonly logService: LogService) {}

    @Get()
    async getLogs() {
        return { status: 'Log service is running' };
    }

    @Post()
    async log(
        @Body()
        logData: {
            code: number;
            level: string;
            message: string;
            context: string;
            timestamp?: string;
            metadata?: object;
            serviceName?: string;
        },
        @Headers('request-id') requestId: string,
    ) {
        // If serviceId is not in headers, extract it from the body (or handle default value)
        const requestIdField = requestId || 'anonymous - ' + Math.random().toString(36).slice(2, 9); // Generate random ID if not provided

        const {
            code,
            level,
            message,
            context,
            timestamp = new Date().toISOString(),
            metadata = {},
            serviceName = 'system',
        } = logData;

        // Prepare log object with dynamically assigned service
        const logMessage = {
            code,
            level,
            message,
            requestId: requestIdField,
            context,
            timestamp,
            metadata,
            service: serviceName, // Attach the service (API key, service ID, etc.)
        };

        await this.logService.sendLogToLogstash(logMessage);
        return { status: 'Log received', timestamp };
    }
}
