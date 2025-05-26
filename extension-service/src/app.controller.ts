import { Controller, Get, Post } from '@nestjs/common';
import { AppService } from './app.service';
import { CrawlerService } from './crawler/crawler.service';

@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly crawlerService: CrawlerService, // Assuming CrawlerService is injected here
  ) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Get('health')
  getHealth(): string {
    return 'OK';
  }

  @Post('crawl')
  async crawl(): Promise<{ status: string; message: string, data?: any }> {
    try {
      const result = await this.crawlerService.crawlAllAppsAndActions();
      return {
        status: 'success',
        message: 'Crawling completed successfully.',
        data: result,
      }
    } catch (error) {
      console.error('Crawl failed:', error);
      return {
        status: 'error',
        message: `Crawling failed: ${error.message}`,
      }
    }
  }
}
