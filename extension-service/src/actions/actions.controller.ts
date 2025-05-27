import { Controller, Get, Param, Query } from '@nestjs/common';
import { ActionsService } from './actions.service';

@Controller('actions')
export class ActionsController {
  constructor(
		private readonly actionService: ActionsService,
  ) {}

	@Get('')
	async getAllActions(@Query('appKey') appKey: string): Promise<{ status: string; message: string; data?: any, metadata?: any }> {
		try {
			const { result, meta } = await this.actionService.getAllActions(appKey);
			return {
				status: 'success',
				message: 'Actions fetched successfully.',
				data: result,
				metadata: meta,
			};
		} catch (error) {
			console.error('Error fetching actions:', error);
			return {
				status: 'error',
				message: `Failed to fetch actions: ${error.message}`,
			};
		}
	}

	@Get(':actionEnum')
	async getActionByEnum(
		@Param('actionEnum') actionEnum: string,
		@Query('appKey') appKey: string,
	): Promise<{ status: string; message: string; data?: any }> {
		try {
			const action = await this.actionService.getActionByEnum(actionEnum, appKey);
			return {
				status: 'success',
				message: 'Action fetched successfully.',
				data: action,
			};
		} catch (error) {
			console.error('Error fetching action:', error);
			return {
				status: 'error',
				message: `Failed to fetch action: ${error.message}`,
			};
		}
	}
}
