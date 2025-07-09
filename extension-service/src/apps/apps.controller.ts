import { AppsService } from '@/apps/apps.service';
import { Controller, Get, Headers, Param, Query } from '@nestjs/common';

@Controller('apps')
export class AppsController {
		constructor(
			private readonly appsService: AppsService,
	) {}

	@Get('')
	async getAllApps(
		@Query('page') page?: number,
		@Query('category') category?: string, // Optional, can be used for filtering apps by category
		@Query('sortBy') sortBy?: string, // Optional, can be used for sorting apps
		@Query('sortOrder') sortOrder?: 'asc' | 'desc', // Optional, can be used for sorting order
		@Query('search') search?: string, // Optional, can be used for searching apps by name or key
		@Query('limit') limit?: number, // Optional, can be used to set a custom limit
		@Query('connected') connected?: string, // Optional, can be used to filter connected apps
		@Headers('X-User-Id') userId?: string, // Optional, can be used to filter apps by user ID
): Promise<{ status: string; message: string; data?: any; metadata?: any }> {
	try {
		const { result, meta } = await this.appsService.getAllApps({
			page: page ? parseInt(page.toString(), 10) : 1,
			limit: limit ? parseInt(limit.toString(), 10) : 24, // Default limit, can be adjusted or made dynamic
			category: category, // Optional category filter
			sortBy: sortBy, // Optional sorting field
			sortOrder: sortOrder, // Optional sorting order
			search: search, // Optional search term
			userId: userId, // Optional user ID for filtering apps
			connected: connected === "true" ? true : (connected === "false" ? false : undefined), // Optional filter for connected apps
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
