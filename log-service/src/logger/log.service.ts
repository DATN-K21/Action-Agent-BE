import { Injectable, Logger, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import { RabbitMQHelper } from 'src/helpers/rabbitmq.helper';

@Injectable()
export class LogService implements OnModuleInit, OnModuleDestroy {
    private readonly logger = new Logger(LogService.name);
    private rabbitMQHelper: RabbitMQHelper;

    constructor(private readonly configService: ConfigService) {
        this.rabbitMQHelper = new RabbitMQHelper(configService);
    }

    async onModuleInit() {
        // Start RabbitMQ consumer on module initialization
        await this.rabbitMQHelper.initializeConsumer(this.processLogMessage.bind(this));
    }

    async onModuleDestroy() {
        // Gracefully close RabbitMQ connection when the module is destroyed
        await this.rabbitMQHelper.closeConnection();
    }

    async processLogMessage(logMessage: any): Promise<void> {
        try {
            await axios.post('http://logstash:5044', logMessage); // Adjust Logstash URL as needed
            this.logger.log('Log message sent to Logstash:', logMessage);
        } catch (error) {
            this.logger.error('Failed to send log to Logstash:', error.message);
        }
    }

    async sendLogToLogstash(logMessage: any): Promise<void> {
        try {
            await axios.post('http://logstash:5044', logMessage); // Adjust Logstash URL as needed
        } catch (error) {
            this.logger.error('Failed to send log to Logstash:', error.message);
        }
    }
}
