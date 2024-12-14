import { Module } from '@nestjs/common';
import { LogController } from './log.controller'; // Your log controller
import { LogService } from './log.service'; // Your log service if applicable

@Module({
    controllers: [LogController],
    providers: [LogService], // Add LogService if you need business logic in your logger
})
export class LogModule {}
