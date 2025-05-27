import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { App } from './schema/apps.schema';

@Injectable()
export class AppsService {
	constructor(
    @InjectModel(App.name) private readonly appsModel: Model<App>,
	) {}

	async getAllApps({ page, limit } = { page: 1, limit: 10 }) : Promise<{
		 result: App[]; 
		 meta: {
			count: number;
			total: number;
			limit: number,
			page: number;
			totalPage: number
	 	}
		}> {
		const skip = (page - 1) * limit;
		const total = await this.appsModel.countDocuments();
		const apps = await this.appsModel.find()
			.skip(skip)
			.limit(limit)
			.sort({ key: 1 })
			.exec();

		return {
			result: apps,
			meta: {
				count: apps.length,
				total,
				page: +page,
				totalPage: Math.ceil(total / limit),
				limit,
			},
		};
		
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
