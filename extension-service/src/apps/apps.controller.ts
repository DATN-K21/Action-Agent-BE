import { AppsService } from '@/apps/apps.service';
import { Controller, Get, Param, Query } from '@nestjs/common';

@Controller('apps')
export class AppsController {
		constructor(
			private readonly appsService: AppsService,
	) {}

	@Get('')
	async getAllApps(
		@Query('page') page: number = 1,
		@Query('limit') limit: number = 10, // Optional, can be used to set a custom limit
): Promise<{ status: string; message: string; data?: any; metadata?: any }> {
		try {
			const { result, meta } = await this.appsService.getAllApps({
				page: page,
				limit: limit, // Default limit, can be adjusted or made dynamic
			});
			return {
				status: 'success',
				message: 'Apps fetched successfully.',
				data: result,
				metadata: meta,
			}
		} catch (error) {
			console.error('Error fetching apps:', error);
			return {
				status: 'error',
				message: `Failed to fetch apps: ${error.message}`,
			}
		}

	}

	// Get detail of a specific app by key
	@Get(':key')
	async getAppByKey(@Param('key') key: string): Promise<{ status: string; message: string; data?: any }> {
		try {
			const app = await this.appsService.getAppByKey(key);
			return {
				status: 'success',
				message: 'App fetched successfully.',
				data: app,
			};
		} catch (error) {
			console.error('Error fetching app:', error);
			return {
				status: 'error',
				message: `Failed to fetch app: ${error.message}`,
			};
		}
	}
}
