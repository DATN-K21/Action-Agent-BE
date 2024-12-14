import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { LogModule } from './logger/log.module';
import { ConfigModule } from '@nestjs/config';
import { HealthController } from './health/health.controller';

@Module({
    imports: [
        ConfigModule.forRoot({
            isGlobal: true, // Make the config available globally
            envFilePath: '.env', // Path to your environment file
        }),
        LogModule,
    ],
    controllers: [AppController, HealthController],
    providers: [AppService],
})
export class AppModule {}
