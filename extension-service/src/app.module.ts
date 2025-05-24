import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ActionsModule } from './actions/actions.module';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AppsModule } from './apps/apps.module';
import { EnvironmentConfig } from './configs/environment.config';
import { CrawlerModule } from './crawler/crawler.module';

@Module({
  imports: [
    MongooseModule.forRoot(EnvironmentConfig.DATABASE_URL || 'mongodb://localhost:27017/composio'),
    AppsModule, 
    ActionsModule,
    CrawlerModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
