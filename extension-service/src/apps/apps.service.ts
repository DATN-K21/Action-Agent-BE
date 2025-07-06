import { AiServiceAxiosInstance } from '@/configs/axios.config';
import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { FilterQuery, Model, Types } from 'mongoose';
import { App, AppDocument } from './schema/apps.schema';

export interface GetAllAppsParams {
	cursor?: string;
	limit?: number;
	category?: string,
	sortBy?: string,
	sortOrder?: string,
	search?: string,
	userId?: string, // Optional, can be used to filter apps by user
}

export interface CursorPaginationResponse {
	result: App[];
	meta: {
		limit: number,
		nextCursor: string | null,
		hasMore: boolean,
	};
}

export interface ConnectedAppResponse {
	id: string;
	userId: string;
	extensionEnum: string;
	extensionName: string;
	connectionStatus: 'PENDING' | 'CONNECTED' | 'FAILED';
	connectedAccountId: string;
	authScheme: string;
	authValue: string;
	createdAt: string;
}

@Injectable()
export class AppsService {
	constructor(
    @InjectModel(App.name) private readonly appsModel: Model<App>,
	) {}

	async getAllApps(params: GetAllAppsParams): Promise<CursorPaginationResponse> {
		const filter: FilterQuery<AppDocument> = {};
		const {
			cursor,
			limit = 12, // Default limit if not provided
			category,
			sortBy,
			sortOrder,
			search,
			userId,
		} = params;
    if (cursor) {
			if (Types.ObjectId.isValid(cursor) === false) {
				throw new BadRequestException('Invalid cursor');
      }
      filter._id = { $ne: null, $gt: new Types.ObjectId(cursor) };
    }
		if (category) {
			filter.categories = { $in: [category] };
		}
		if (search) {
			const searchRegex = new RegExp(search, 'i'); // Case-insensitive search
			filter.$or = [
				{ name: searchRegex },
				{ key: searchRegex },
			];
		}
		const sortOptions: Record<string, 1 | -1> = {};
		if (sortBy) {
			sortOptions[sortBy] = sortOrder === 'desc' ? -1 : 1;
		} else {
			sortOptions.key = 1; // Default sort by key ascending
		}
		if (userId) {
			const connectedExtensions = await this.getConnectedApps(userId);
			const connectedAppKeys = connectedExtensions.map(app => app.extensionEnum);
			// Filter apps based on connected app keys
			filter.key = { $in: connectedAppKeys };
		}


		const apps: AppDocument[] = await this.appsModel.find(filter)
		.sort(sortOptions)
		.limit(limit + 1)
		.exec();

		const hasMore: boolean = apps.length > limit;
		let nextCursor: string | null = null;

    if (hasMore) {
      apps.pop();
			const lastApp = apps[apps.length - 1] as AppDocument & { _id: Types.ObjectId } | undefined;
			nextCursor = lastApp
				? lastApp._id.toHexString()
				: null;
    }

		return {
			result: apps,
			meta: {
				limit,
				nextCursor,
				hasMore,
			},
		};
	}

	async getConnectedApps(userId: string): Promise<ConnectedAppResponse[]> {
		if (!userId) {
			throw new BadRequestException('User ID is required');
		}
		try {
			const connectedApps = await AiServiceAxiosInstance.get(`connected-extension/get-all?maxPerPage=100`, {
				headers: {
					'X-User-Id': userId,
					'X-User-Role': 'User',
				}
			});
			
			return connectedApps?.data?.connectedExtensions as ConnectedAppResponse[];
		} catch (error) {
			console.error('Error fetching connected apps:', error);
			throw new InternalServerErrorException('Failed to fetch connected apps');
		}
	}

	async getAppByKey(key: string): Promise<App | null> {
		if (!key) {
			throw new Error('App key is required');
		}
		const app = await this.appsModel.findOne({ key }).exec();
		if (!app) {
			throw new Error(`App with key: ${key} not found`);
		}
		return app;
	}
}
