import { ActionSchema } from '@/actions/schema/action.schema';
import { AppSchema } from '@/apps/schema/apps.schema';
import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { CrawlerController } from './crawler.controller';
import { CrawlerService } from './crawler.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: 'App', schema: AppSchema }, // Replace with actual App schema import
      { name: 'Action', schema: ActionSchema }, // Replace with actual Action schema import
    ]),
  ], // No additional imports needed for this module
  controllers: [CrawlerController],
  providers: [CrawlerService],
  exports: [CrawlerService], // Exporting the service if needed in other modules
})
export class CrawlerModule {}
