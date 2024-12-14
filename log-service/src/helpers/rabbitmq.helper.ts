import * as amqp from 'amqplib';
import { Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

export class RabbitMQHelper {
    private readonly logger = new Logger(RabbitMQHelper.name);
    private connection: amqp.Connection | null = null;
    private channel: amqp.Channel | null = null;
    private rabbitMQ: {
        USER: string;
        PASS: string;
        HOST: string;
        PORT: string;
        QUEUE: string;
    };

    constructor(private configService: ConfigService) {
        this.rabbitMQ = {
            USER: this.configService.get<string>('RABBITMQ_USER'),
            PASS: this.configService.get<string>('RABBITMQ_PASS'),
            HOST: this.configService.get<string>('RABBITMQ_HOST'),
            PORT: this.configService.get<string>('RABBITMQ_PORT'),
            QUEUE: this.configService.get<string>('RABBITMQ_QUEUE'),
        };
    }

    async initializeConsumer(onMessage: (message: any) => Promise<void>): Promise<void> {
        const { HOST, PORT, QUEUE, USER, PASS } = this.rabbitMQ;
        const connectionUrl = `amqp://${USER}:${PASS}@${HOST}:${PORT}`;
        console.log('connectionUrl: ', connectionUrl);
        try {
            this.connection = await amqp.connect(connectionUrl);
            this.channel = await this.connection.createChannel();

            await this.channel.assertQueue(QUEUE, { durable: true });
            this.logger.log(`RabbitMQ initialized. Listening on queue: ${QUEUE}`);

            this.channel.consume(QUEUE, async msg => {
                if (msg) {
                    const content = JSON.parse(msg.content.toString());
                    await onMessage(content);
                    this.channel?.ack(msg);
                }
            });
        } catch (error) {
            console.log('Rabbit MQ config: ');
            console.log(this.rabbitMQ);
            this.logger.error('Failed to initialize RabbitMQ consumer:', error.message);
            throw error;
        }
    }

    async closeConnection(): Promise<void> {
        try {
            await this.channel?.close();
            await this.connection?.close();
            this.logger.log('RabbitMQ connection closed.');
        } catch (error) {
            this.logger.error('Failed to close RabbitMQ connection:', error.message);
        }
    }
}
