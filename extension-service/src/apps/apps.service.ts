import { AiServiceAxiosInstance } from '@/configs/axios.config';
import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { FilterQuery, Model } from 'mongoose';
import { App, AppDocument } from './schema/apps.schema';

export interface GetAllAppsParams {
	page?: number;
	limit?: number;
	category?: string,
	sortBy?: string,
	sortOrder?: 'asc' | 'desc',
	search?: string,
	userId?: string, // Optional, can be used to filter apps by user
	connected?: boolean, // Optional, can be used to filter connected apps
}

export interface UserSpecifiedApp {
	id: string;
	key: string;
	name: string;
	displayName: string;
	description: string;
	logo: string;
	actionsCount: number;
	categories: string[];
	tags: string[];
	enabled: boolean;
	noAuth: boolean;
	connected?: boolean; // Optional, indicates if the app is connected for a specific user
}

export interface CursorPaginationResponse {
	result: UserSpecifiedApp[];
	meta: {
		count: number,
		limit: number,
		total: number,
		page: number,
		totalPages: number,
	};
}

export interface ConnectedAppResponse {
	id: string;
	userId: string;
	extensionEnum: string;
	extensionName: string;
	connectionStatus: 'pending' | 'success' | 'failed';
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

	populateFilters = (params: GetAllAppsParams, keys: string[]): FilterQuery<AppDocument> => {
		const filter: FilterQuery<AppDocument> = {};
		const {
			category,
			search,
			connected,
			userId,
		} = params;

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
		if (userId) {
			if (connected === true) {
				filter.key = { $in: keys };
			} else if (connected === false) {
				filter.key = { $nin: keys };
			}
		}
		return filter;
	}

	sanitizeApps(
		apps: AppDocument[],
		keys: string[] = [], 
		userId?: string,
	): UserSpecifiedApp[] {
		const userSpecifiedApps: UserSpecifiedApp[] = apps.map(app => {
			const appObj = app;
			return {
				id: appObj._id.toString(),
				key: appObj.key,
				name: appObj.name,
				displayName: appObj.displayName,
				description: appObj.description,
				logo: appObj.logo,
				actionsCount: appObj.actionsCount || 0,
				categories: appObj.categories,
				tags: appObj.tags,
				enabled: appObj.enabled,
				noAuth: appObj.noAuth,
				connected: userId ? keys.includes(appObj.key) : false,
			} as UserSpecifiedApp;
		});
		return userSpecifiedApps;
	}

	async getAllApps(params: GetAllAppsParams): Promise<CursorPaginationResponse> {
		let connectedAppKeys: string[] = [];
		const { page, limit, userId, sortBy, sortOrder } = params;

		if (userId) {
			const connectedExtensions = await this.getConnectedApps(userId);
			connectedAppKeys = connectedExtensions.map(app => app.extensionName);
		}
		const filter: FilterQuery<AppDocument> = this.populateFilters(params, connectedAppKeys);
		
		const pipeline: any[] = [];
		pipeline.push({ $match: filter });
    
		const sortOptions: Record<string, 1 | -1> = {};
		if (sortBy) {
			sortOptions[sortBy] = sortOrder === 'desc' ? -1 : 1;
		} else {
			sortOptions.key = 1;
		}
		sortOptions.id = 1;

		// Only get total count suitable for filter
		const totalCount = await this.appsModel.countDocuments(filter).exec();
		const totalPages = Math.ceil(totalCount / limit);

		pipeline.push({ $sort: sortOptions });
		const skip = (page - 1) * limit;
		pipeline.push({ $skip: skip });
		pipeline.push({ $limit: limit });

		const apps = await this.appsModel.aggregate(pipeline).exec();

		const userSpecifiedApps = this.sanitizeApps(apps, connectedAppKeys, userId);
		return {
			result: userSpecifiedApps,
			meta: {
				count: userSpecifiedApps.length,
				limit,
				total: totalCount,
				page,
				totalPages,
			},
		};
	}

	async getConnectedApps(userId: string): Promise<ConnectedAppResponse[]> {
		if (!userId) {
			throw new BadRequestException('User ID is required');
		}
		try {
			const connectedApps = await AiServiceAxiosInstance.get(`/connected-extension/get-all?maxPerPage=100`, {
				headers: {
					'X-User-Id': userId,
					'X-User-Role': 'User',
				}
			});
			
			return connectedApps?.data?.connectedExtensions?.filter(
				(app: ConnectedAppResponse) => app.connectionStatus === 'success'
			) as ConnectedAppResponse[];
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
